"""Evaluate FaceVault's face pipeline on LFW (or any one-folder-per-person dataset).

    cd backend
    python -m evaluation.evaluate_lfw --download-to ~/datasets          # fetch original LFW, then evaluate
    python -m evaluation.evaluate_lfw --lfw-dir /path/to/lfw            # LFW already on disk

Stages (see evaluation/README.md for the protocol and how to read the results):
  1. Extract: MTCNN detection + FaceNet embedding with the app's own functions (cached on disk).
  2. Verification: how well do embedding distances separate same / different people?
  3. Batch clustering: all faces uploaded at once, sweeping eps and min_samples
     (chosen on a tune split of identities, reported on a disjoint test split).
  4. Incremental clustering: replay the app's upload-by-upload behaviour in random orders.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import sys
import time
import zipfile
from pathlib import Path

import numpy as np

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:  # allows `python evaluation/evaluate_lfw.py` as well as `-m`
    sys.path.insert(0, str(BACKEND))

from evaluation.datasets import download_lfw, load_folder_dataset  # noqa: E402
from evaluation.metrics import (  # noqa: E402
    clustering_report,
    pair_similarity_histograms,
    roc_from_histograms,
    threshold_table,
    verification_summary,
)
from evaluation.simulate import (  # noqa: E402
    batch_assignments,
    best_by,
    best_conservative,
    simulate_uploads,
    split_identities,
    sweep_batch,
)
from ml.clustering import DEFAULT_EPS, DEFAULT_MIN_SAMPLES, normalize  # noqa: E402
from ml.defaults import STANDARDIZE_EMBEDDINGS  # noqa: E402

CACHE_VERSION = 1
CHECKPOINT_EVERY = 250
CACHE_REPLACE_ATTEMPTS = 6   # Windows refuses to replace a file that antivirus/indexers briefly hold open
CACHE_REPLACE_DELAY = 0.2    # seconds, doubled after every failed attempt
OFF_CENTER_LIMIT = 0.2  # chosen face further than 20% of the image width from the centre looks suspect
# Cached arrays: "emb" is pixels / 255, "emb_std" is (pixels - 127.5) / 128. "app" is whichever the app uses.
SCALINGS = {"emb": "pixels / 255", "emb_std": "(pixels - 127.5) / 128"}
VARIANTS = {
    "app": "emb_std" if STANDARDIZE_EMBEDDINGS else "emb",
    "ablation": "emb" if STANDARDIZE_EMBEDDINGS else "emb_std",
}

SCORE_COLUMNS = [
    ("ari", "ARI", "{:.3f}"),
    ("pair_precision", "pair P", "{:.3f}"),
    ("pair_recall", "pair R", "{:.3f}"),
    ("pair_f1", "pair F1", "{:.3f}"),
    ("assigned_frac", "in a person", "{:.1%}"),
    ("wrong_face_frac", "wrong person*", "{:.2%}"),
    ("n_people", "people", "{:.0f}"),
    ("n_identities", "identities", "{:.0f}"),
]


# ----------------------------------------------------------------------------- extraction

def cache_key(samples, root):
    digest = hashlib.sha1()
    digest.update(f"v{CACHE_VERSION}".encode())
    for path, identity in samples:
        digest.update(f"{os.path.relpath(path, root)}|{identity}\n".encode())
    return digest.hexdigest()


def read_cache(cache_path, key, names):
    """(arrays, images done) from the cache, or None if there is no usable cache for this dataset."""
    if not cache_path.exists():
        return None
    try:
        # Closed straight away: Windows cannot replace a file that is still open.
        with np.load(cache_path, allow_pickle=False) as cached:
            if str(cached["key"]) != key:
                return None
            return {name: cached[name].copy() for name in names}, int(cached["done"])
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(f"Ignoring unreadable cache {cache_path.name} ({error}); starting from scratch")
        return None


def write_cache(cache_path, key, done, data):
    """Write the cache atomically (temporary file, then replace), retrying if Windows has the target locked."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = cache_path.with_suffix(".tmp.npz")
    with open(temporary, "wb") as handle:
        np.savez(handle, key=key, done=done, **data)
    for attempt in range(CACHE_REPLACE_ATTEMPTS):
        try:
            os.replace(temporary, cache_path)
            return
        except PermissionError:
            if attempt == CACHE_REPLACE_ATTEMPTS - 1:
                raise
            time.sleep(CACHE_REPLACE_DELAY * 2 ** attempt)


def save_checkpoint(cache_path, key, done, data):
    """Best-effort cache write. Returns False (after a warning) instead of raising.

    The cache only saves time, so a failed write must never lose a long run: the data is still in memory.
    """
    from tqdm import tqdm

    try:
        write_cache(cache_path, key, done, data)
        return True
    except OSError as error:
        tqdm.write(f"  warning: could not save the cache ({error}); continuing without this checkpoint",
                   file=sys.stderr)
        return False


def extract_features(samples, root, cache_path):
    """Detect and embed one face per image, resuming from `cache_path` when it exists."""
    from tqdm import tqdm

    from ml.detect_faces import MIN_FACE_CONFIDENCE, detect_faces
    from ml.generate_embeddings import generate_embedding
    from ml.image_utils import crop_face, open_oriented

    n = len(samples)
    key = cache_key(samples, root)
    data = {
        "emb": np.full((n, 512), np.nan, dtype=np.float32),
        "emb_std": np.full((n, 512), np.nan, dtype=np.float32),
        "found": np.zeros(n, dtype=bool),
        "failed": np.zeros(n, dtype=bool),
        "n_faces": np.zeros(n, dtype=np.int16),
        "off_center": np.full(n, np.nan, dtype=np.float32),
        "confidence": np.full(n, np.nan, dtype=np.float32),
    }
    done = 0
    cached = read_cache(cache_path, key, data) if cache_path else None
    if cached:
        data, done = cached
        print(f"Resuming from cache: {done}/{n} images already processed ({cache_path.name})")

    def save(upto):
        if cache_path:
            save_checkpoint(cache_path, key, upto, data)

    started = time.time()
    for i in tqdm(range(done, n), desc="detect + embed", unit="img", initial=done, total=n):
        try:
            image = open_oriented(samples[i][0])
            faces = [f for f in detect_faces(image) if f["confidence"] >= MIN_FACE_CONFIDENCE]
        except Exception as error:  # corrupt / unreadable file: count it, keep going
            data["failed"][i] = True
            tqdm.write(f"  skipped {samples[i][0]}: {error}", file=sys.stderr)
            faces = []
        data["n_faces"][i] = len(faces)
        if faces:
            width, height = image.size

            def off_center(face):
                x, y, w, h = face["box"]
                return math.hypot(x + w / 2 - width / 2, y + h / 2 - height / 2) / width

            # LFW images are centred on the labelled person; other faces are bystanders.
            face = min(faces, key=off_center)
            _, _, crop = crop_face(image, face["box"])
            data["emb"][i] = generate_embedding(crop, standardize=False)
            data["emb_std"][i] = generate_embedding(crop, standardize=True)
            data["found"][i] = True
            data["off_center"][i] = off_center(face)
            data["confidence"][i] = face["confidence"]
        if (i + 1) % CHECKPOINT_EVERY == 0:
            save(i + 1)
    save(n)
    if n > done:
        print(f"Processed {n - done} images in {time.time() - started:.0f}s "
              f"({(time.time() - started) / (n - done) * 1000:.0f} ms/image)")
    return data


# ----------------------------------------------------------------------------- reporting helpers

def parse_range(text):
    start, stop, step = (float(part) for part in text.split(":"))
    return [round(float(v), 4) for v in np.arange(start, stop + step / 2, step)]


def markdown_table(rows, columns):
    """columns: [(key, header, format)] -> pipe table; key 'label' is printed as text."""
    lines = ["| " + " | ".join(header for _, header, _ in columns) + " |",
             "|" + "|".join("---" for _ in columns) + "|"]
    for row in rows:
        cells = []
        for key, _, fmt in columns:
            value = row.get(key, float("nan"))
            if isinstance(value, str):
                cells.append(value)
            else:
                cells.append("n/a" if value is None or (isinstance(value, float) and math.isnan(value))
                             else fmt.format(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def mean_std(reports):
    """Per-key mean and std over a list of report dicts."""
    out = {}
    for key in reports[0]:
        values = np.array([r[key] for r in reports], dtype=float)
        defined = values[~np.isnan(values)]  # e.g. wrong-person share is undefined while nobody is assigned
        out[key] = float(defined.mean()) if len(defined) else float("nan")
        out[key + "_std"] = float(defined.std()) if len(defined) else float("nan")
    return out


def write_csv(path, rows):
    if not rows:
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def config_label(name, cfg):
    return f"{name} (eps={cfg['eps']:g}, min_samples={cfg['min_samples']})"


# ----------------------------------------------------------------------------- the evaluation

def evaluate_variant(name, embeddings, ids, args, eps_values, min_samples_values, log=print):
    """All stages for one embedding variant. Returns (results dict, csv rows, plot data)."""
    tune, test = split_identities(ids, args.tune_fraction, args.seed)
    if args.tune_fraction <= 0 or not tune.any() or not test.any():
        log("  (no usable tune/test split: tuning and reporting on the SAME faces, results are optimistic)")
        tune = test = np.ones(len(ids), dtype=bool)
    split_note = {"tune_faces": int(tune.sum()), "tune_identities": int(len(set(ids[tune]))),
                  "test_faces": int(test.sum()), "test_identities": int(len(set(ids[test])))}
    log(f"  tune split: {split_note['tune_faces']} faces / {split_note['tune_identities']} people; "
          f"test split: {split_note['test_faces']} faces / {split_note['test_identities']} people")

    unit = normalize(embeddings)

    # 2. verification (threshold-free; nothing is tuned on it, so every face is used)
    log(f"  verification: comparing all pairs of {len(ids)} faces ...")
    same_hist, diff_hist = pair_similarity_histograms(unit, ids)
    verification = verification_summary(same_hist, diff_hist)
    verification["operating_points"] = threshold_table(same_hist, diff_hist, eps_values)

    # 3. batch sweep: tune on one set of people, score on another
    log(f"  batch sweep: {len(eps_values)} eps x {len(min_samples_values)} min_samples on the tune and test splits ...")
    sweep_tune = sweep_batch(unit[tune], ids[tune], eps_values, min_samples_values)
    sweep_test = sweep_batch(unit[test], ids[test], eps_values, min_samples_values)
    app_cfg = {"eps": DEFAULT_EPS, "min_samples": DEFAULT_MIN_SAMPLES}
    tuned = best_by(sweep_tune, "ari")
    conservative = best_conservative(sweep_tune, 0.99)
    configs = {"app config": app_cfg,
               "tuned (best ARI on tune)": {"eps": tuned["eps"], "min_samples": tuned["min_samples"]}}
    if conservative:
        configs["conservative (max recall, precision >= .99 on tune)"] = {
            "eps": conservative["eps"], "min_samples": conservative["min_samples"]}
    seen_cfgs, unique_configs = set(), {}
    for label, cfg in configs.items():  # drop configs that coincide with an earlier one
        marker = (cfg["eps"], cfg["min_samples"])
        if marker not in seen_cfgs:
            seen_cfgs.add(marker)
            unique_configs[label] = cfg

    main_rows, incremental_rows, curves = [], [], {}
    test_unit, test_ids = unit[test], ids[test]
    for label, cfg in unique_configs.items():
        batch = clustering_report(test_ids, batch_assignments(test_unit, cfg["eps"], cfg["min_samples"]))
        main_rows.append({"label": f"{config_label(label, cfg)} - batch", **batch})

        if args.skip_incremental:
            continue
        log(f"  incremental replay: {label}, {args.orders} orders (each replays {len(test_ids)} uploads) ...")
        reports, snapshots_per_order = [], []
        for order_seed in range(args.orders):
            order = np.random.default_rng(args.seed + 1000 + order_seed).permutation(len(test_ids))
            assignments, snapshots = simulate_uploads(
                test_unit, order, cfg["eps"], cfg["min_samples"],
                batch_size=args.batch_size, checkpoints=args.checkpoints)
            reports.append(clustering_report(test_ids, assignments))
            snapshots_per_order.append(snapshots)
            log(f"    order {order_seed + 1}/{args.orders} done")
            incremental_rows.append({"variant": name, "config": label, **cfg, "order_seed": order_seed, **reports[-1]})
        summary = mean_std(reports)
        main_rows.append({"label": f"{config_label(label, cfg)} - incremental (mean of {args.orders} orders)", **summary})
        main_rows.append({"label": "    std over orders", **{k[:-4]: v for k, v in summary.items() if k.endswith("_std")}})

        if label == "app config":
            curve = []
            for point in range(len(args.checkpoints)):
                at_checkpoint = [clustering_report(test_ids[s[point][1]], s[point][2]) for s in snapshots_per_order]
                curve.append({"fraction": args.checkpoints[point], "n_seen": snapshots_per_order[0][point][0],
                              **mean_std(at_checkpoint)})
            curves[label] = curve

    results = {
        "split": split_note,
        "verification": verification,
        "configs": {label: cfg for label, cfg in unique_configs.items()},
        "tuned_on_tune_split": tuned,
        "sweep_test": sweep_test,
        "main": main_rows,
        "learning_curve": curves,
    }
    csv_rows = ([{"variant": name, "split": "tune", **row} for row in sweep_tune]
                + [{"variant": name, "split": "test", **row} for row in sweep_test])
    plot_data = {"roc": roc_from_histograms(same_hist, diff_hist), "sweep_test": sweep_test, "curves": curves,
                 "app_cfg": app_cfg, "tuned_cfg": unique_configs["tuned (best ARI on tune)"]
                 if "tuned (best ARI on tune)" in unique_configs else app_cfg}
    return results, csv_rows, incremental_rows, plot_data


def make_plots(out_dir, plot_data):
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed: skipping plots (pip install -r requirements-eval.txt)")
        return []
    written = []
    names = list(plot_data)
    first = plot_data[names[0]]

    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    for name in names:
        fpr, tpr = plot_data[name]["roc"]
        ax.plot(np.maximum(fpr, 1e-6), tpr, label=f"{name}: {SCALINGS[VARIANTS[name]]}")
    ax.set_xscale("log")
    ax.set_xlabel("false positive rate (different people judged same)")
    ax.set_ylabel("true positive rate")
    ax.set_title("Face verification ROC")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "roc.png", dpi=150)
    plt.close(fig)
    written.append("roc.png")

    rows = first["sweep_test"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for min_samples in sorted({r["min_samples"] for r in rows}):
        subset = [r for r in rows if r["min_samples"] == min_samples]
        axes[0].plot([r["eps"] for r in subset], [r["ari"] for r in subset], marker="o", label=f"min_samples={min_samples}")
    app_ms = first["app_cfg"]["min_samples"]
    subset = [r for r in rows if r["min_samples"] == app_ms] or rows
    axes[1].plot([r["eps"] for r in subset], [r["pair_precision"] for r in subset], marker="o", label="pairwise precision")
    axes[1].plot([r["eps"] for r in subset], [r["pair_recall"] for r in subset], marker="o", label="pairwise recall")
    axes[1].plot([r["eps"] for r in subset], [r["wrong_face_frac"] for r in subset], marker="o", ls="--", label="wrong-person faces")
    for ax in axes:
        ax.axvline(first["app_cfg"]["eps"], color="grey", ls=":", label="app eps")
        ax.set_xlabel("eps (cosine distance)")
        ax.grid(alpha=0.3)
        ax.legend()
    axes[0].set_ylabel("ARI (test identities)")
    axes[1].set_title(f"min_samples={app_ms}")
    axes[0].set_title("Batch DBSCAN: effect of eps")
    fig.tight_layout()
    fig.savefig(out_dir / "sweep_eps.png", dpi=150)
    plt.close(fig)
    written.append("sweep_eps.png")

    if first["curves"]:
        curve = first["curves"]["app config"]
        fig, ax = plt.subplots(figsize=(5.5, 4.5))
        x = [c["fraction"] for c in curve]
        for key, label in (("pair_precision", "pairwise precision"), ("pair_recall", "pairwise recall"), ("ari", "ARI")):
            y, spread = np.array([c[key] for c in curve]), np.array([c[key + "_std"] for c in curve])
            ax.plot(x, y, marker="o", label=label)
            ax.fill_between(x, y - spread, y + spread, alpha=0.2)
        ax.set_xlabel("share of photos uploaded so far")
        ax.set_title("Incremental clustering as the library grows")
        ax.grid(alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(out_dir / "incremental_curve.png", dpi=150)
        plt.close(fig)
        written.append("incremental_curve.png")
    return written


def build_report(protocol, all_results, plots):
    out = ["# FaceVault evaluation", "", "## Protocol", ""]
    out += [f"- {line}" for line in protocol]
    for name, results in all_results.items():
        scaling = SCALINGS[VARIANTS[name]]
        title = {"app": f"app embeddings as shipped, input {scaling}",
                 "ablation": f"ablation, input {scaling}"}[name]
        v = results["verification"]
        out += ["", f"## Results: {title}", "", "### Verification (all faces, threshold-free)", "",
                f"AUC {v['auc']:.4f} | EER {v['eer']:.2%} | TPR at FPR=0.1% {v['tpr_at_fpr_0.001']:.2%} "
                f"| {v['n_same_pairs']:,} same-person and {v['n_diff_pairs']:,} different-person pairs", "",
                "Same-person rule \"cosine distance <= eps\" (this is what eps means in the app):", "",
                markdown_table(v["operating_points"], [("eps", "eps", "{:.2f}"), ("tpr", "same pairs accepted", "{:.1%}"),
                                                        ("fpr", "different pairs accepted", "{:.3%}")]),
                "", "### Clustering on the test identities", "",
                f"Configs: {json.dumps(results['configs'])}", "",
                markdown_table(results["main"], [("label", "configuration", "{}")] + SCORE_COLUMNS), "",
                "\\* wrong person = of the faces filed under a person, the share filed under the wrong one "
                "(unassigned faces are not counted here but cost recall).", ""]
        if results["learning_curve"]:
            curve = results["learning_curve"]["app config"]
            out += ["### Incremental clustering as the library grows (app config)", "",
                    markdown_table(curve, [("fraction", "share uploaded", "{:.0%}"), ("n_seen", "faces", "{:.0f}"),
                                           ("pair_precision", "pair P", "{:.3f}"), ("pair_recall", "pair R", "{:.3f}"),
                                           ("ari", "ARI", "{:.3f}"), ("assigned_frac", "in a person", "{:.1%}")]), ""]
    if plots:
        out += ["## Figures", ""] + [f"![{p}]({p})" for p in plots] + [""]
    out += ["## Caveats", "",
            "- LFW is mostly frontal, well-lit celebrity photos, so scores are optimistic for family photo libraries.",
            "- Identities were capped per person; pairwise scores are dominated by people with many images.",
            "- Scores use the face closest to the image centre (the labelled person); the app stores every face it finds.",
            ""]
    return "\n".join(out)


# ----------------------------------------------------------------------------- main

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--lfw-dir", help="folder with one sub-folder of images per person")
    source.add_argument("--download-to", help="download original LFW here with torchvision (needs network)")
    parser.add_argument("--min-images", type=int, default=2, help="drop people with fewer images (default 2)")
    parser.add_argument("--max-per-identity", type=int, default=20, help="cap images per person (default 20; 0 = no cap)")
    parser.add_argument("--max-identities", type=int, default=0, help="random subset of people for a quick run (0 = all)")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--tune-fraction", type=float, default=0.5,
                        help="share of people used to choose eps; the rest are the test set (0 = no split)")
    parser.add_argument("--eps", default="0.20:0.70:0.05", help="start:stop:step (default 0.20:0.70:0.05)")
    parser.add_argument("--min-samples", default="2,3,5")
    parser.add_argument("--orders", type=int, default=5, help="random upload orders to replay (default 5)")
    parser.add_argument("--batch-size", type=int, default=1, help="images per simulated upload (default 1)")
    parser.add_argument("--checkpoints", default="0.1,0.25,0.5,0.75,1.0")
    parser.add_argument("--skip-incremental", action="store_true")
    parser.add_argument("--ablate-preprocessing", action="store_true",
                        help="also evaluate the other FaceNet input scaling (the one the app does not use)")
    parser.add_argument("--cache-dir", default=str(BACKEND / "evaluation" / "cache"))
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--out-dir", default=str(BACKEND / "evaluation" / "results"))
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):  # show progress in a redirected log straight away
        sys.stdout.reconfigure(line_buffering=True)
    args.checkpoints = [float(c) for c in args.checkpoints.split(",")]
    eps_values = parse_range(args.eps)
    min_samples_values = [int(v) for v in args.min_samples.split(",")]

    root = args.lfw_dir or download_lfw(os.path.expanduser(args.download_to))
    samples = load_folder_dataset(root, args.min_images, args.max_per_identity or None,
                                  args.max_identities or None, args.seed)
    print(f"{len(samples)} images of {len({i for _, i in samples})} people from {root}")

    cache_path = None if args.no_cache else Path(args.cache_dir) / f"features_{cache_key(samples, root)[:12]}.npz"
    data = extract_features(samples, root, cache_path)

    found = data["found"]
    ids_all = np.array([identity for _, identity in samples])
    ids = np.unique(ids_all[found], return_inverse=True)[1]
    multi = int((data["n_faces"][found] > 1).sum())
    off = int((data["off_center"][found] > OFF_CENTER_LIMIT).sum())
    print(f"Detection (confidence >= app gate): {int(found.sum())}/{len(samples)} images have a face "
          f"({found.mean():.1%}); {int(data['failed'].sum())} unreadable; {multi} have several faces; "
          f"{off} chose a face far from the centre")
    if found.sum() < 10:
        raise SystemExit("Too few detected faces to evaluate.")
    singletons = int((np.bincount(ids) == 1).sum())

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    variants = ["app"] + (["ablation"] if args.ablate_preprocessing else [])
    all_results, sweep_rows, incremental_rows, plot_data = {}, [], [], {}
    for name in variants:
        print(f"\n== {name} embeddings ==")
        embeddings = data[VARIANTS[name]][found].astype(float)
        results, sweeps, incrementals, plots = evaluate_variant(
            name, embeddings, ids, args, eps_values, min_samples_values)
        all_results[name] = results
        sweep_rows += sweeps
        incremental_rows += incrementals
        plot_data[name] = plots
        print(markdown_table(results["main"], [("label", "configuration", "{}")] + SCORE_COLUMNS))

    protocol = [
        f"Dataset: {root}; {len(samples)} images of {len(set(ids_all.tolist()))} people "
        f"(people with at least {args.min_images} images; at most {args.max_per_identity or 'all'} per person; seed {args.seed}).",
        f"Detection: MTCNN with the app's gate (confidence >= 0.95) found a face in {int(found.sum())} images "
        f"({found.mean():.1%}); {int((~found).sum())} images dropped. People with only one detected face: {singletons}.",
        "Embedding: the app's FaceNet pipeline on the app's face crop (tight box, no margin).",
        f"Split: {args.tune_fraction:.0%} of people choose eps/min_samples (best ARI); results are reported on the "
        "disjoint remaining people.",
        f"Incremental: faces arrive {args.batch_size} at a time in {args.orders} random orders; after each batch the "
        "app's clustering logic runs over every face that has no person yet.",
        f"App config: eps={DEFAULT_EPS:g}, min_samples={DEFAULT_MIN_SAMPLES}.",
    ]
    plots = [] if args.no_plots else make_plots(out_dir, plot_data)
    (out_dir / "results.json").write_text(json.dumps(
        {"protocol": protocol, "results": all_results}, indent=2, default=float))
    write_csv(out_dir / "sweep_batch.csv", sweep_rows)
    write_csv(out_dir / "incremental_runs.csv", incremental_rows)
    (out_dir / "report.md").write_text(build_report(protocol, all_results, plots))
    print(f"\nWrote {out_dir}/report.md, results.json, sweep_batch.csv, incremental_runs.csv"
          + (f" and {', '.join(plots)}" if plots else ""))


if __name__ == "__main__":
    main()
