"""Replay FaceVault's clustering on precomputed embeddings.

Everything here calls ml.clustering.plan_assignments, the same function the app's
cluster_faces() uses, so the numbers describe the app and not a re-implementation.
No database and no ML models are needed.
"""
import numpy as np

from evaluation.metrics import NOISE, clustering_report
from ml.clustering import normalize, plan_assignments


def batch_assignments(embeddings, eps, min_samples):
    """All faces uploaded at once: no people exist yet, so only the DBSCAN step runs."""
    embeddings = np.asarray(embeddings, dtype=float)
    _, labels = plan_assignments(embeddings, np.empty((0, embeddings.shape[1])), eps, min_samples)
    return labels


def simulate_uploads(embeddings, order, eps, min_samples, batch_size=1, match_eps=None, checkpoints=()):
    """Faces arrive in `order`, `batch_size` at a time, like uploads to the app.

    After each batch the app's logic runs over every face that has no person yet
    (earlier leftovers plus the new ones): match against existing people's centroids,
    then DBSCAN the rest into new people. People and their members never change
    afterwards, which is the "stable identity" behaviour being tested.

    checkpoints: fractions (0-1] of faces seen at which to snapshot the state.
    Returns (assignments, snapshots): assignments[i] is the person index of face i
    (-1 if never assigned); snapshots is a list of (n_seen, seen_indices, assignments).
    """
    X = normalize(embeddings)
    n, dim = X.shape
    order = np.asarray(order)
    assignments = np.full(n, NOISE, dtype=int)
    person_sums = np.zeros((n, dim))  # sum of unit embeddings per person; normalised = centroid
    n_people = 0
    pool = []  # faces without a person: older leftovers first, like the app's id order
    snapshots = []
    pending = sorted(checkpoints)

    for start in range(0, n, batch_size):
        pool.extend(order[start:start + batch_size].tolist())
        members = np.array(pool)

        matched, labels = plan_assignments(
            X[members], normalize(person_sums[:n_people]) if n_people else np.empty((0, dim)),
            eps, min_samples, match_eps,
        )

        leftovers = []
        label_to_person = {}
        for face, person, label in zip(members, matched, labels):
            if person < 0 and label >= 0:
                if label not in label_to_person:
                    label_to_person[label] = n_people
                    n_people += 1
                person = label_to_person[label]
            if person < 0:
                leftovers.append(face)
                continue
            assignments[face] = person
            person_sums[person] += X[face]
        pool = leftovers

        seen = min(start + batch_size, n)
        while pending and seen >= pending[0] * n:
            pending.pop(0)
            snapshots.append((seen, order[:seen].copy(), assignments[order[:seen]].copy()))

    return assignments, snapshots


def sweep_batch(embeddings, true_ids, eps_values, min_samples_values):
    """clustering_report rows for every (eps, min_samples), clustering all faces at once."""
    rows = []
    for min_samples in min_samples_values:
        for eps in eps_values:
            labels = batch_assignments(embeddings, eps, min_samples)
            rows.append({"eps": float(eps), "min_samples": int(min_samples),
                         **clustering_report(true_ids, labels)})
    return rows


def best_by(rows, key="ari"):
    """Row with the highest `key` (first one wins ties)."""
    return max(rows, key=lambda row: row[key])


def best_conservative(rows, min_precision=0.99):
    """Highest-recall row whose pairwise precision is at least min_precision (None if none)."""
    eligible = [row for row in rows if row["pair_precision"] >= min_precision]
    return max(eligible, key=lambda row: row["pair_recall"]) if eligible else None


def split_identities(ids, tune_fraction, seed):
    """Identity-disjoint split: returns boolean masks (tune, test) over faces.

    Tuning hyper-parameters on one set of people and reporting on another avoids
    the optimism of picking eps on the very faces being scored.
    """
    ids = np.asarray(ids)
    unique = np.unique(ids)
    rng = np.random.default_rng(seed)
    rng.shuffle(unique)
    cut = int(round(len(unique) * tune_fraction))
    tune_ids = set(unique[:cut].tolist())
    tune = np.array([i in tune_ids for i in ids.tolist()])
    return tune, ~tune
