import itertools
import unittest

import numpy as np
from sklearn.metrics import roc_auc_score

from evaluation.metrics import (
    NOISE,
    clustering_report,
    pair_similarity_histograms,
    pairwise_prf,
    singletonize,
    threshold_table,
    verification_summary,
)
from evaluation.simulate import (
    batch_assignments,
    best_by,
    best_conservative,
    simulate_uploads,
    split_identities,
    sweep_batch,
)


def planted_embeddings(n_identities=12, per_identity=5, dim=64, sigma=0.06, seed=0):
    """Unit-ish embeddings: each identity is a random direction plus small noise."""
    rng = np.random.default_rng(seed)
    centers = rng.standard_normal((n_identities, dim))
    centers /= np.linalg.norm(centers, axis=1, keepdims=True)
    ids = np.repeat(np.arange(n_identities), per_identity)
    return centers[ids] + sigma * rng.standard_normal((len(ids), dim)), ids


def brute_force_pairwise(true_ids, labels):
    tp = pred = actual = 0
    for i, j in itertools.combinations(range(len(true_ids)), 2):
        same_cluster = labels[i] == labels[j]
        same_person = true_ids[i] == true_ids[j]
        tp += same_cluster and same_person
        pred += same_cluster
        actual += same_person
    return tp / pred if pred else 1.0, tp / actual if actual else 1.0


class ClusteringMetricTests(unittest.TestCase):
    def test_singletonize_gives_each_unassigned_face_its_own_cluster(self):
        out = singletonize([0, NOISE, 1, NOISE, 0])
        self.assertEqual(len(set(out.tolist())), 4)  # clusters 0, 1 plus two singletons
        self.assertEqual(out[0], out[4])

    def test_pairwise_precision_recall_match_brute_force(self):
        rng = np.random.default_rng(1)
        for _ in range(20):
            true_ids = rng.integers(0, 6, size=40)
            labels = rng.integers(0, 8, size=40)
            precision, recall, _ = pairwise_prf(true_ids, labels)
            expected = brute_force_pairwise(true_ids.tolist(), labels.tolist())
            self.assertAlmostEqual(precision, expected[0])
            self.assertAlmostEqual(recall, expected[1])

    def test_perfect_clustering(self):
        report = clustering_report([0, 0, 1, 1, 2, 2], [5, 5, 3, 3, 9, 9])
        for key in ("ari", "pair_precision", "pair_recall", "pair_f1", "v_measure", "pure_person_frac"):
            self.assertAlmostEqual(report[key], 1.0, msg=key)
        self.assertEqual(report["wrong_face_frac"], 0.0)
        self.assertEqual(report["assigned_frac"], 1.0)
        self.assertEqual(report["n_people"], 3)

    def test_merging_two_people_hurts_precision_and_purity_not_recall(self):
        report = clustering_report([0, 0, 1, 1], [0, 0, 0, 0])
        self.assertAlmostEqual(report["pair_recall"], 1.0)
        self.assertAlmostEqual(report["pair_precision"], 2 / 6)
        self.assertAlmostEqual(report["wrong_face_frac"], 0.5)
        self.assertEqual(report["pure_person_frac"], 0.0)

    def test_splitting_a_person_hurts_recall_not_precision(self):
        report = clustering_report([0, 0, 0, 0], [0, 0, 1, 1])
        self.assertAlmostEqual(report["pair_precision"], 1.0)
        self.assertAlmostEqual(report["pair_recall"], 2 / 6)
        self.assertEqual(report["wrong_face_frac"], 0.0)

    def test_everything_unassigned(self):
        report = clustering_report([0, 0, 1, 1], [NOISE] * 4)
        self.assertEqual(report["assigned_frac"], 0.0)
        self.assertEqual(report["n_people"], 0)
        self.assertEqual(report["pair_recall"], 0.0)
        self.assertEqual(report["pair_f1"], 0.0)
        self.assertTrue(np.isnan(report["wrong_face_frac"]))

    def test_unassigned_faces_do_not_count_as_wrong_but_cost_recall(self):
        report = clustering_report([0, 0, 0, 1, 1], [0, 0, NOISE, 1, 1])
        self.assertEqual(report["wrong_face_frac"], 0.0)
        self.assertAlmostEqual(report["assigned_frac"], 4 / 5)
        self.assertLess(report["pair_recall"], 1.0)


class VerificationMetricTests(unittest.TestCase):
    def setUp(self):
        embeddings, self.ids = planted_embeddings(n_identities=15, per_identity=6, sigma=0.12, seed=3)
        self.unit = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    def brute_force_sims(self):
        sims = self.unit @ self.unit.T
        i, j = np.triu_indices(len(self.ids), k=1)
        return sims[i, j], self.ids[i] == self.ids[j]

    def test_histogram_counts_every_pair_once(self):
        same, diff = pair_similarity_histograms(self.unit, self.ids, block=17)
        n = len(self.ids)
        self.assertEqual(same.sum() + diff.sum(), n * (n - 1) // 2)
        self.assertEqual(same.sum(), 15 * (6 * 5 // 2))

    def test_auc_matches_scikit_learn(self):
        same, diff = pair_similarity_histograms(self.unit, self.ids)
        sims, is_same = self.brute_force_sims()
        self.assertAlmostEqual(verification_summary(same, diff)["auc"], roc_auc_score(is_same, sims), places=3)

    def test_separable_data_has_zero_equal_error_rate(self):
        embeddings, ids = planted_embeddings(sigma=0.02)
        unit = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        summary = verification_summary(*pair_similarity_histograms(unit, ids))
        self.assertAlmostEqual(summary["auc"], 1.0, places=3)
        self.assertAlmostEqual(summary["eer"], 0.0, places=3)

    def test_threshold_table_matches_direct_counts(self):
        same, diff = pair_similarity_histograms(self.unit, self.ids)
        sims, is_same = self.brute_force_sims()
        for row in threshold_table(same, diff, [0.2, 0.4, 0.6]):
            accepted = sims >= 1 - row["eps"]
            self.assertAlmostEqual(row["tpr"], accepted[is_same].mean(), places=2)
            self.assertAlmostEqual(row["fpr"], accepted[~is_same].mean(), places=2)

    def test_no_pairs_gives_nan_not_a_crash(self):
        summary = verification_summary(np.zeros(10, dtype=int), np.zeros(10, dtype=int))
        self.assertTrue(np.isnan(summary["auc"]))


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.embeddings, self.ids = planted_embeddings(n_identities=10, per_identity=6, sigma=0.05, seed=5)

    def test_batch_clustering_recovers_planted_identities(self):
        report = clustering_report(self.ids, batch_assignments(self.embeddings, eps=0.4, min_samples=2))
        self.assertGreater(report["ari"], 0.99)

    def test_incremental_upload_recovers_identities_in_any_order(self):
        for seed in range(3):
            order = np.random.default_rng(seed).permutation(len(self.ids))
            assignments, _ = simulate_uploads(self.embeddings, order, eps=0.4, min_samples=2)
            self.assertGreater(clustering_report(self.ids, assignments)["ari"], 0.95, f"order seed {seed}")

    def test_assigned_faces_never_change_person_later(self):
        order = np.random.default_rng(0).permutation(len(self.ids))
        final, snapshots = simulate_uploads(
            self.embeddings, order, eps=0.4, min_samples=2, checkpoints=(0.25, 0.5, 0.75))
        self.assertEqual(len(snapshots), 3)
        for n_seen, seen, snapshot in snapshots:
            self.assertEqual(len(seen), n_seen)
            already_assigned = snapshot != NOISE
            np.testing.assert_array_equal(final[seen][already_assigned], snapshot[already_assigned])

    def test_batch_size_changes_nothing_when_everything_arrives_in_one_batch(self):
        order = np.arange(len(self.ids))
        one_shot, _ = simulate_uploads(self.embeddings, order, 0.4, 2, batch_size=len(order))
        np.testing.assert_array_equal(
            clustering_report(self.ids, one_shot)["ari"],
            clustering_report(self.ids, batch_assignments(self.embeddings, 0.4, 2))["ari"])

    def test_sweep_and_selection_helpers(self):
        rows = sweep_batch(self.embeddings, self.ids, eps_values=[0.05, 0.4, 0.9], min_samples_values=[2])
        self.assertEqual(len(rows), 3)
        self.assertEqual(best_by(rows)["eps"], 0.4)  # 0.05 splits identities, 0.9 merges them all
        self.assertEqual(best_conservative(rows, min_precision=0.99)["eps"], 0.4)
        self.assertIsNone(best_conservative([{"pair_precision": 0.5, "pair_recall": 1.0}], 0.99))

    def test_identity_split_is_disjoint_and_reproducible(self):
        tune, test = split_identities(self.ids, tune_fraction=0.5, seed=7)
        self.assertFalse(set(self.ids[tune]) & set(self.ids[test]))
        self.assertEqual(len(set(self.ids[tune])), 5)
        tune_again, _ = split_identities(self.ids, tune_fraction=0.5, seed=7)
        np.testing.assert_array_equal(tune, tune_again)


if __name__ == "__main__":
    unittest.main()
