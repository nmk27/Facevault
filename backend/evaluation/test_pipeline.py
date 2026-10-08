import inspect
import json
import os
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from evaluation.datasets import download_lfw, load_folder_dataset
from evaluation.evaluate_lfw import (
    build_report,
    evaluate_variant,
    make_plots,
    CACHE_REPLACE_ATTEMPTS,
    markdown_table,
    mean_std,
    parse_range,
    read_cache,
    save_checkpoint,
    write_cache,
)
from evaluation.test_metrics import planted_embeddings


def make_folder(root, layout):
    """layout: {identity: n_images}; creates empty .jpg files (names only matter here)."""
    for identity, count in layout.items():
        folder = Path(root) / identity
        folder.mkdir(parents=True)
        for i in range(count):
            (folder / f"{identity}_{i + 1:04d}.jpg").write_bytes(b"")
    (Path(root) / "README.txt").write_text("not an identity folder")
    (Path(root) / ".hidden").mkdir()


class DatasetLoaderTests(unittest.TestCase):
    def test_min_images_filter_and_layout(self):
        with tempfile.TemporaryDirectory() as root:
            make_folder(root, {"Ann": 3, "Bob": 1, "Cy": 2})

            samples = load_folder_dataset(root, min_images=2)

        self.assertEqual({identity for _, identity in samples}, {"Ann", "Cy"})
        self.assertEqual(len(samples), 5)
        self.assertEqual([i for _, i in samples], sorted(i for _, i in samples))

    def test_caps_are_seeded_and_applied(self):
        with tempfile.TemporaryDirectory() as root:
            make_folder(root, {f"P{n:02d}": 12 for n in range(10)})

            first = load_folder_dataset(root, max_per_identity=4, max_identities=6, seed=3)
            again = load_folder_dataset(root, max_per_identity=4, max_identities=6, seed=3)
            other = load_folder_dataset(root, max_per_identity=4, max_identities=6, seed=4)

        self.assertEqual(first, again)
        self.assertNotEqual(first, other)
        self.assertEqual(len({i for _, i in first}), 6)
        self.assertEqual(len(first), 24)

    def test_empty_dataset_exits_with_a_message(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(SystemExit):
                load_folder_dataset(root, min_images=2)

    def test_download_helper_matches_the_installed_torchvision_signature(self):
        # The download itself needs network access; at least check the API we call still exists.
        try:
            from torchvision.datasets import LFWPeople
        except ImportError:
            self.skipTest("torchvision not installed")
        parameters = inspect.signature(LFWPeople.__init__).parameters
        for name in ("root", "split", "image_set", "download"):
            self.assertIn(name, parameters)
        self.assertTrue(callable(download_lfw))


class CacheTests(unittest.TestCase):
    """The feature cache must survive Windows file locking: it is what makes a 15-minute run resumable."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "cache" / "features.npz"
        self.data = {"emb": np.arange(6, dtype=np.float32).reshape(2, 3), "found": np.array([True, False])}

    def test_round_trip(self):
        write_cache(self.path, "key", 5, self.data)

        arrays, done = read_cache(self.path, "key", self.data)

        self.assertEqual(done, 5)
        np.testing.assert_array_equal(arrays["emb"], self.data["emb"])
        np.testing.assert_array_equal(arrays["found"], self.data["found"])

    def test_missing_other_dataset_and_corrupt_caches_are_ignored(self):
        self.assertIsNone(read_cache(self.path, "key", self.data))  # no file yet
        write_cache(self.path, "key", 5, self.data)
        self.assertIsNone(read_cache(self.path, "another dataset", self.data))
        self.path.write_bytes(b"this is not an npz file")
        self.assertIsNone(read_cache(self.path, "key", self.data))

    def test_reading_closes_the_file_so_windows_can_replace_it_later(self):
        loaded = mock.MagicMock()
        loaded.__enter__.return_value = {"key": np.array("key"), "done": np.array(3), **self.data}
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(b"placeholder")

        with mock.patch("evaluation.evaluate_lfw.np.load", return_value=loaded):
            read_cache(self.path, "key", self.data)

        loaded.__exit__.assert_called_once()

    def test_replace_is_retried_when_the_target_is_briefly_locked(self):
        real_replace = os.replace
        locked = [PermissionError(5, "Access is denied"), PermissionError(5, "Access is denied")]

        def flaky_replace(source, destination):
            if locked:
                raise locked.pop()
            real_replace(source, destination)

        with mock.patch("evaluation.evaluate_lfw.os.replace", side_effect=flaky_replace) as replace, \
                mock.patch("evaluation.evaluate_lfw.time.sleep") as sleep:
            write_cache(self.path, "key", 7, self.data)

        self.assertEqual(replace.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertEqual(read_cache(self.path, "key", self.data)[1], 7)

    def test_write_gives_up_after_the_last_attempt(self):
        with mock.patch("evaluation.evaluate_lfw.os.replace", side_effect=PermissionError(5, "Access is denied")) as replace, \
                mock.patch("evaluation.evaluate_lfw.time.sleep"):
            with self.assertRaises(PermissionError):
                write_cache(self.path, "key", 1, self.data)

        self.assertEqual(replace.call_count, CACHE_REPLACE_ATTEMPTS)

    def test_a_failed_checkpoint_warns_but_never_stops_the_run(self):
        with mock.patch("evaluation.evaluate_lfw.write_cache", side_effect=PermissionError(5, "Access is denied")):
            self.assertFalse(save_checkpoint(self.path, "key", 1, self.data))
        self.assertTrue(save_checkpoint(self.path, "key", 2, self.data))
        self.assertEqual(read_cache(self.path, "key", self.data)[1], 2)


class HelperTests(unittest.TestCase):
    def test_parse_range_is_inclusive_and_free_of_float_drift(self):
        self.assertEqual(parse_range("0.2:0.4:0.05"), [0.2, 0.25, 0.3, 0.35, 0.4])

    def test_mean_std_ignores_undefined_values_quietly(self):
        out = mean_std([{"a": 1.0, "b": float("nan")}, {"a": 3.0, "b": float("nan")}])
        self.assertEqual(out["a"], 2.0)
        self.assertEqual(out["a_std"], 1.0)
        self.assertTrue(np.isnan(out["b"]))

    def test_markdown_table_formats_values_and_missing_numbers(self):
        table = markdown_table([{"label": "x", "v": 0.5}, {"label": "y", "v": float("nan")}],
                               [("label", "name", "{}"), ("v", "value", "{:.1%}")])
        self.assertIn("| x | 50.0% |", table)
        self.assertIn("| y | n/a |", table)


class EvaluateVariantTests(unittest.TestCase):
    """The whole evaluation on synthetic embeddings (no models, no dataset needed)."""

    def setUp(self):
        self.embeddings, self.ids = planted_embeddings(n_identities=24, per_identity=5, sigma=0.05, seed=2)
        self.args = types.SimpleNamespace(
            tune_fraction=0.5, seed=0, skip_incremental=False, orders=2, batch_size=1,
            checkpoints=[0.5, 1.0])

    def run_variant(self, **overrides):
        vars(self.args).update(overrides)
        return evaluate_variant("app", self.embeddings, self.ids, self.args, [0.2, 0.4, 0.6], [2, 3],
                                log=lambda *args, **kwargs: None)

    def test_results_are_complete_and_sensible(self):
        results, sweep_rows, incremental_rows, plot_data = self.run_variant()

        self.assertEqual(results["split"]["tune_identities"] + results["split"]["test_identities"], 24)
        self.assertGreater(results["verification"]["auc"], 0.99)
        batch_rows = [r for r in results["main"] if r["label"].endswith("batch")]
        self.assertTrue(batch_rows)
        for row in batch_rows:
            self.assertGreater(row["ari"], 0.9)
        self.assertEqual(len(sweep_rows), 2 * 3 * 2)  # tune+test x eps x min_samples
        self.assertEqual(len(incremental_rows), 2 * len(results["configs"]))
        self.assertEqual([c["fraction"] for c in results["learning_curve"]["app config"]], [0.5, 1.0])
        json.dumps(results, default=float)  # must be serialisable

    def test_tuning_and_test_people_are_disjoint(self):
        results, *_ = self.run_variant()
        split = results["split"]
        self.assertEqual(split["tune_faces"] + split["test_faces"], len(self.ids))

    def test_skip_incremental_and_no_split(self):
        results, _, incremental_rows, _ = self.run_variant(skip_incremental=True, tune_fraction=0)

        self.assertEqual(incremental_rows, [])
        self.assertEqual(results["split"]["tune_faces"], results["split"]["test_faces"])
        self.assertFalse(results["learning_curve"])

    def test_report_mentions_every_section(self):
        results, *_ = self.run_variant()
        report = build_report(["protocol line"], {"app": results}, [])
        for text in ("## Protocol", "protocol line", "Verification", "Clustering on the test identities",
                     "Incremental clustering as the library grows", "## Caveats"):
            self.assertIn(text, report)

    def test_plots_are_written_when_matplotlib_is_available(self):
        try:
            import matplotlib  # noqa: F401
        except ImportError:
            self.skipTest("matplotlib not installed (optional: requirements-eval.txt)")
        *_, plot_data = self.run_variant()
        with tempfile.TemporaryDirectory() as out:
            written = make_plots(Path(out), {"app": plot_data})
            self.assertEqual(sorted(written), ["incremental_curve.png", "roc.png", "sweep_eps.png"])
            for name in written:
                self.assertGreater((Path(out) / name).stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
