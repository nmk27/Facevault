"""Draw the figures used in README.md and docs/PROJECT_REPORT.md from the committed evaluation results.

    python docs/make_figures.py          # writes docs/images/fig-*.png

Input:  backend/evaluation/results_eps_fine/{results.json, sweep_batch.csv}
Needs:  numpy, matplotlib (pip install -r backend/requirements-eval.txt)

In those result files the variant called "app" is the original input scaling (pixels / 255) and
"standardized" is FaceNet's own scaling, (pixels - 127.5) / 128, which the app uses now.
"""
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "backend" / "evaluation" / "results_eps_fine"
OUT = ROOT / "docs" / "images"

# Validated with the palette checker (light surface): blue and orange pass every categorical check;
# the two blues pass the ordinal-ramp check used for before/after bars.
SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, BLUE_LIGHT = "#2a78d6", "#eb6834", "#86b6ef"

OLD, NEW = "app", "standardized"  # variant keys in the result files
LABEL = {OLD: "Original input scaling (pixels / 255)", NEW: "FaceNet input scaling (current)"}
COLOR = {OLD: ORANGE, NEW: BLUE}
MARKER = {OLD: "s", NEW: "o"}  # a second identity channel besides colour
OLD_EPS, NEW_EPS = 0.4, 0.2

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK_2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.linewidth": 1.0,
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": GRID, "grid.linewidth": 1.0, "grid.linestyle": "-",
    "xtick.labelsize": 9, "ytick.labelsize": 9, "axes.labelsize": 10,
})


def load():
    results = json.loads((RESULTS / "results.json").read_text())["results"]
    with open(RESULTS / "sweep_batch.csv") as handle:
        sweep = [{k: (float(v) if k not in ("variant", "split") else v) for k, v in row.items()}
                 for row in csv.DictReader(handle)]
    return results, sweep


def series(sweep, variant, split, key, min_samples=2):
    rows = sorted((r for r in sweep if r["variant"] == variant and r["split"] == split
                   and r["min_samples"] == min_samples), key=lambda r: r["eps"])
    return [r["eps"] for r in rows], [r[key] for r in rows]


def style_axes(ax, grid_axis="y"):
    ax.grid(True, axis=grid_axis)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def title(fig, heading, subheading):
    fig.text(0.012, 0.975, heading, fontsize=13, fontweight="semibold", color=INK, va="top")
    fig.text(0.012, 0.915, subheading, fontsize=9.5, color=INK_2, va="top")


def legend_keys(fig, variants=(NEW, OLD), y=0.015):
    handles = [Line2D([0], [0], color=COLOR[v], lw=2, marker=MARKER[v], markersize=6, label=LABEL[v])
               for v in variants]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.012, y), ncol=2, frameon=False,
               fontsize=9, labelcolor=INK_2, handlelength=2.2, columnspacing=2.0)


def mark_defaults(ax, y_text, ymax):
    for eps, text, ha in ((NEW_EPS, "new default\neps 0.2", "right"), (OLD_EPS, "old default\neps 0.4", "right")):
        ax.axvline(eps, color=AXIS, lw=1.0, zorder=1)
        ax.text(eps - 0.004, y_text, text, fontsize=8.5, color=MUTED, ha=ha, va="top", linespacing=1.15)
    ax.set_ylim(0, ymax)


# ---------------------------------------------------------------- 1. before and after
def fig_before_after(results):
    def row(variant, prefix):
        return next(r for r in results[variant]["main"]
                    if r["label"].startswith(prefix) and "incremental" in r["label"])

    before, now = row(OLD, "app config"), row(NEW, "tuned")
    split = results[NEW]["split"]
    panels = [
        ("Faces filed under\nthe wrong person", "wrong_face_frac", True, "lower is better"),
        ("Pairwise\nprecision", "pair_precision", False, "higher is better"),
        ("Pairwise\nrecall", "pair_recall", False, "higher is better"),
        ("Faces placed\nin a person", "assigned_frac", True, "higher is better"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(11.2, 4.1))
    fig.subplots_adjust(left=0.03, right=0.99, top=0.70, bottom=0.17, wspace=0.28)
    for ax, (name, key, percent, hint) in zip(axes, panels):
        values = [before[key], now[key]]
        shown = [v * 100 for v in values] if percent else values
        top = max(shown) * 1.3 if key == "wrong_face_frac" else (110 if percent else 1.12)
        bars = ax.bar([0, 1], shown, width=0.46, color=[BLUE_LIGHT, BLUE], zorder=3)
        def fmt(v):
            if not percent:
                return f"{v:.3f}"  # a ratio between 0 and 1, never a percentage
            return f"{v:.2f}%" if v < 1 else f"{v:.1f}%"

        for bar, value, text in zip(bars, shown, [fmt(v) for v in shown]):
            ax.text(bar.get_x() + bar.get_width() / 2, value + top * 0.025, text, ha="center", va="bottom",
                    fontsize=10.5, color=INK, fontweight="semibold")
        ax.set_xticks([0, 1], ["Before", "Now"], fontsize=10, color=INK_2)
        ax.set_ylim(0, top)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.set_title(name, fontsize=10.5, color=INK, loc="left", pad=22, linespacing=1.2)
        ax.text(0, 1.035, hint, transform=ax.transAxes, fontsize=8.5, color=MUTED, va="bottom")
        ax.tick_params(length=0)
    title(fig, "Retuning the clustering cut wrong-person errors from 1 in 6 faces to about 1 in 1,400",
          f"Held-out LFW people ({split['test_identities']} people, {split['test_faces']:,} faces), faces uploaded one at a time, "
          "mean of 5 random orders")
    fig.legend(handles=[Patch(color=BLUE_LIGHT, label="Before: pixels / 255 input scaling, eps 0.4"),
                        Patch(color=BLUE, label="Now: FaceNet input scaling, eps 0.2")],
               loc="lower left", bbox_to_anchor=(0.012, 0.01), ncol=2, frameon=False, fontsize=9, labelcolor=INK_2)
    fig.savefig(OUT / "fig-before-after.png", dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------- 2. ARI against eps
def fig_eps_sweep(sweep):
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.5), sharey=True)
    fig.subplots_adjust(left=0.065, right=0.99, top=0.76, bottom=0.2, wspace=0.06)
    for ax, split, heading in ((axes[0], "tune", "People used to choose eps (840 people)"),
                               (axes[1], "test", "Held-out people (840 people)")):
        for variant in (OLD, NEW):
            eps, ari = series(sweep, variant, split, "ari")
            ax.plot(eps, ari, color=COLOR[variant], lw=2, marker=MARKER[variant], markersize=6,
                    markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3)
        best = max(zip(*series(sweep, NEW, split, "ari")), key=lambda p: p[1])
        ax.plot(*best, marker="o", markersize=12, markerfacecolor="none", markeredgecolor=BLUE, markeredgewidth=1.2,
                zorder=4)
        # When the best eps is the default, its own label already sits above it: put this one to the right.
        offset, ha = ((16, 4), "left") if best[0] == NEW_EPS else ((0, 13), "center")
        ax.annotate(f"best: eps {best[0]:g}", xy=best, xytext=offset, textcoords="offset points",
                    fontsize=8.5, color=INK_2, ha=ha, va="bottom")
        style_axes(ax)
        mark_defaults(ax, 0.985, 1.0)
        ax.set_title(heading, fontsize=10.5, color=INK, loc="left", pad=8)
        ax.set_xlabel("eps (cosine distance threshold)")
        ax.set_xlim(0.09, 0.41)
    axes[0].set_ylabel("ARI (1 = perfect grouping)")
    axes[1].tick_params(labelleft=False)
    title(fig, "Clustering quality collapses once eps passes about 0.3",
          "DBSCAN over all faces at once (min_samples 2). The two halves of the people disagree on the best eps, "
          "so 0.2 to 0.25 is a range, not a point")
    legend_keys(fig)
    fig.savefig(OUT / "fig-eps-sweep.png", dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------- 3. precision against recall
def fig_precision_recall(sweep):
    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    fig.subplots_adjust(left=0.1, right=0.97, top=0.82, bottom=0.2)
    for variant in (OLD, NEW):
        eps, recall = series(sweep, variant, "test", "pair_recall")
        _, precision = series(sweep, variant, "test", "pair_precision")
        keep = [i for i, e in enumerate(eps) if e <= 0.3]
        ax.plot([recall[i] for i in keep], [precision[i] for i in keep], color=COLOR[variant], lw=2,
                marker=MARKER[variant], markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3)
        if variant == NEW:
            where = {0.15: ((0, -13), "center", "top"), 0.2: ((-6, -15), "right", "top"),
                     0.25: ((9, 2), "left", "center"), 0.3: ((9, 0), "left", "center")}
            for i in keep:
                if eps[i] in where:
                    offset, ha, va = where[eps[i]]
                    text = f"eps {eps[i]:g}" + (" (default)" if eps[i] == NEW_EPS else "")
                    ax.annotate(text, xy=(recall[i], precision[i]), xytext=offset, textcoords="offset points",
                                fontsize=8.5, color=INK_2, ha=ha, va=va)
                if eps[i] == NEW_EPS:
                    ax.plot(recall[i], precision[i], marker="o", markersize=13, markerfacecolor="none",
                            markeredgecolor=BLUE, markeredgewidth=1.2, zorder=4)
    style_axes(ax, "both")
    ax.set_xlim(0, 1.06)
    ax.set_ylim(0.3, 1.03)
    ax.set_xlabel("Pairwise recall (share of same-person pairs grouped together)")
    ax.set_ylabel("Pairwise precision")
    title(fig, "FaceNet scaling gives a better precision/recall trade-off",
          "Held-out people, DBSCAN over all faces at once; each point is one eps, from 0.10 to 0.30")
    legend_keys(fig, y=0.01)
    fig.savefig(OUT / "fig-precision-recall.png", dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------- 4. what eps lets through
def fig_eps_error(results):
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.5))
    fig.subplots_adjust(left=0.065, right=0.985, top=0.76, bottom=0.2, wspace=0.22)
    pairs = {v: results[v]["verification"] for v in (OLD, NEW)}
    n_different = pairs[NEW]["n_diff_pairs"]
    for variant in (OLD, NEW):
        points = pairs[variant]["operating_points"]
        eps = [p["eps"] for p in points]
        axes[0].plot(eps, [p["tpr"] * 100 for p in points], color=COLOR[variant], lw=2, marker=MARKER[variant],
                     markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3)
        positive = [(p["eps"], p["fpr"] * 100) for p in points if p["fpr"] > 0]
        axes[1].plot(*zip(*positive), color=COLOR[variant], lw=2, marker=MARKER[variant], markersize=6,
                     markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3)
    for ax, ylabel in zip(axes, ("Same-person pairs accepted (%)", "Different-person pairs accepted (%, log scale)")):
        style_axes(ax)
        ax.set_xlabel("eps (cosine distance threshold)")
        ax.set_ylabel(ylabel)
        ax.set_xlim(0.09, 0.41)
        for eps in (NEW_EPS, OLD_EPS):
            ax.axvline(eps, color=AXIS, lw=1.0, zorder=1)
    axes[0].set_ylim(0, 100)
    axes[1].set_yscale("log")
    axes[1].set_ylim(1e-6, 1.0)
    for eps, ha in ((NEW_EPS, "right"), (OLD_EPS, "right")):
        axes[0].text(eps - 0.004, 98, f"eps {eps:g}", fontsize=8.5, color=MUTED, ha=ha, va="top")
    where = {NEW_EPS: ((-14, 22), "right"), OLD_EPS: ((-6, -46), "right")}  # offsets in points, into empty space
    for eps, (offset, ha) in where.items():
        point = next(p for p in pairs[NEW]["operating_points"] if abs(p["eps"] - eps) < 1e-9)
        count = point["fpr"] * n_different
        shown = round(count, -2) if count >= 1000 else round(count)  # two or three digits is all the data supports
        axes[1].annotate(f"about {shown:,.0f} wrong pairs\nout of {n_different / 1e6:.1f} million",
                         xy=(eps, point["fpr"] * 100), xytext=offset, textcoords="offset points", fontsize=8.5,
                         color=INK_2, ha=ha, va="center", linespacing=1.15,
                         arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 1.0, "shrinkA": 2, "shrinkB": 6})
    axes[1].text(0.10, 2e-6, "none at eps 0.10", fontsize=8.5, color=MUTED, ha="left", va="bottom")
    title(fig, "Every extra bit of eps buys recall and lets wrong matches in, exponentially",
          "All pairs of the 7,379 faces (27,724 same-person and 27.2 million different-person pairs); "
          "wrong pairs counted for FaceNet scaling")
    legend_keys(fig)
    fig.savefig(OUT / "fig-eps-error.png", dpi=150)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results, sweep = load()
    fig_before_after(results)
    fig_eps_sweep(sweep)
    fig_precision_recall(sweep)
    fig_eps_error(results)
    print("wrote", ", ".join(sorted(p.name for p in OUT.glob("fig-*.png"))))


if __name__ == "__main__":
    main()
