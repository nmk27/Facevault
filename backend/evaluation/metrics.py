"""Metrics for judging face clustering and face verification.

Pure numpy / scikit-learn, so it can be tested without the ML models.

Conventions
-----------
* Cluster assignments use -1 for "no person" (DBSCAN noise or never matched).
* `clustering_report` treats every unassigned face as its own one-face cluster for
  ARI, pairwise and V-measure scores (the usual convention), and also reports what
  the app would actually *show*: how many faces land in a person and how many of
  those are in the wrong person.
* Pairwise precision / recall are defined as 1.0 when no pair is asserted / no true
  pair exists ("nothing was claimed, so nothing was wrong"); F1 then exposes the
  degenerate case (all singletons give precision 1.0, recall 0.0, F1 0.0).
"""
import numpy as np
from sklearn.metrics import adjusted_rand_score, homogeneity_completeness_v_measure
from sklearn.metrics.cluster import contingency_matrix

NOISE = -1


def singletonize(assignments):
    """Give every unassigned face (-1) its own cluster id."""
    assignments = np.array(assignments, dtype=int)
    noise = assignments == NOISE
    start = assignments.max() + 1 if assignments.size and assignments.max() >= 0 else 0
    assignments[noise] = start + np.arange(noise.sum())
    return assignments


def _pairs(counts):
    counts = np.asarray(counts, dtype=float)
    return float((counts * (counts - 1) / 2).sum())


def pairwise_prf(true_ids, labels):
    """Pairwise precision, recall and F1 of a clustering (labels must not contain -1).

    A pair of faces is "positive" when both faces are in the same cluster; it is
    correct when the two faces are also the same person.
    """
    table = contingency_matrix(true_ids, labels, sparse=True)
    true_positive = _pairs(table.data)
    predicted = _pairs(np.asarray(table.sum(axis=0)).ravel())
    actual = _pairs(np.asarray(table.sum(axis=1)).ravel())
    precision = true_positive / predicted if predicted else 1.0
    recall = true_positive / actual if actual else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def clustering_report(true_ids, assignments):
    """Scores for one clustering of faces with known identities."""
    true_ids = np.asarray(true_ids)
    assignments = np.asarray(assignments, dtype=int)
    assigned = assignments != NOISE
    labels = singletonize(assignments)

    precision, recall, f1 = pairwise_prf(true_ids, labels)
    homogeneity, completeness, v_measure = homogeneity_completeness_v_measure(true_ids, labels)

    n_assigned = int(assigned.sum())
    wrong_face_frac = pure_person_frac = float("nan")
    if n_assigned:
        table = contingency_matrix(true_ids[assigned], assignments[assigned], sparse=True).tocsc()
        majority = np.asarray(table.max(axis=0).todense()).ravel()
        wrong_face_frac = 1.0 - majority.sum() / n_assigned
        pure_person_frac = float((np.diff(table.indptr) == 1).mean())

    return {
        "n_faces": int(len(true_ids)),
        "n_identities": int(len(np.unique(true_ids))),
        "n_people": int(len(np.unique(assignments[assigned]))),
        "assigned_frac": n_assigned / len(true_ids) if len(true_ids) else float("nan"),
        "ari": float(adjusted_rand_score(true_ids, labels)),
        "pair_precision": precision,
        "pair_recall": recall,
        "pair_f1": f1,
        "homogeneity": float(homogeneity),
        "completeness": float(completeness),
        "v_measure": float(v_measure),
        # Of the faces the app would file under a person, the share filed under the wrong one.
        "wrong_face_frac": float(wrong_face_frac),
        # Share of people (clusters) that contain exactly one real identity.
        "pure_person_frac": pure_person_frac,
    }


# --------------------------------------------------------------------------- verification

HISTOGRAM_BINS = 20000  # cosine similarity in [-1, 1] -> resolution 1e-4


def pair_similarity_histograms(unit_embeddings, ids, bins=HISTOGRAM_BINS, block=1000):
    """Histograms of cosine similarity over all same-person and different-person pairs.

    Streams over blocks of rows, so memory stays small even for ~10k faces
    (~50M pairs). Returns (same, different) count arrays of length `bins`.
    """
    X = np.asarray(unit_embeddings, dtype=np.float32)
    ids = np.asarray(ids)
    n = len(X)
    columns = np.arange(n)[None, :]
    same_hist = np.zeros(bins, dtype=np.int64)
    diff_hist = np.zeros(bins, dtype=np.int64)
    for start in range(0, n, block):
        stop = min(start + block, n)
        sims = X[start:stop] @ X.T
        upper = columns > np.arange(start, stop)[:, None]  # each unordered pair once
        same = ids[start:stop, None] == ids[None, :]
        for mask, hist in ((upper & same, same_hist), (upper & ~same, diff_hist)):
            idx = np.clip(((sims[mask] + 1.0) / 2.0 * bins).astype(np.int64), 0, bins - 1)
            hist += np.bincount(idx, minlength=bins)
    return same_hist, diff_hist


def roc_from_histograms(same_hist, diff_hist):
    """(fpr, tpr) as the similarity threshold sweeps from high to low."""
    tpr = np.concatenate([[0.0], np.cumsum(same_hist[::-1]) / max(same_hist.sum(), 1)])
    fpr = np.concatenate([[0.0], np.cumsum(diff_hist[::-1]) / max(diff_hist.sum(), 1)])
    return fpr, tpr


def verification_summary(same_hist, diff_hist, target_fpr=1e-3):
    """Threshold-free verification scores from the pair histograms."""
    if same_hist.sum() == 0 or diff_hist.sum() == 0:
        return {"auc": float("nan"), "eer": float("nan"), f"tpr_at_fpr_{target_fpr:g}": float("nan"),
                "n_same_pairs": int(same_hist.sum()), "n_diff_pairs": int(diff_hist.sum())}
    fpr, tpr = roc_from_histograms(same_hist, diff_hist)
    auc = float(np.sum((fpr[1:] - fpr[:-1]) * (tpr[1:] + tpr[:-1]) / 2))
    fnr = 1.0 - tpr
    closest = int(np.argmin(np.abs(fpr - fnr)))
    return {
        "auc": auc,
        "eer": float((fpr[closest] + fnr[closest]) / 2),
        f"tpr_at_fpr_{target_fpr:g}": float(tpr[fpr <= target_fpr].max()),
        "n_same_pairs": int(same_hist.sum()),
        "n_diff_pairs": int(diff_hist.sum()),
    }


def threshold_table(same_hist, diff_hist, eps_values, bins=HISTOGRAM_BINS):
    """TPR / FPR of the rule "same person if cosine distance <= eps", one row per eps."""
    rows = []
    for eps in eps_values:
        first_bin = int(np.clip((1.0 - eps + 1.0) / 2.0 * bins, 0, bins))
        rows.append({
            "eps": float(eps),
            "tpr": float(same_hist[first_bin:].sum() / same_hist.sum()) if same_hist.sum() else float("nan"),
            "fpr": float(diff_hist[first_bin:].sum() / diff_hist.sum()) if diff_hist.sum() else float("nan"),
        })
    return rows
