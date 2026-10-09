"""Database-free core of FaceVault's face clustering.

`cluster_faces.py` applies these decisions to the database; `evaluation/` runs the
same functions on benchmark data, so what gets measured is what the app runs.
"""
import os

import numpy as np
from sklearn.cluster import DBSCAN

# The app's clustering settings (see backend/.env.example); evaluation/ reads the same ones.
# eps was chosen on LFW people held apart from the ones it is scored on: precision first, and
# a margin before the point (about 0.3) where chained matches merge everyone into huge groups.
DEFAULT_EPS = float(os.getenv("FACE_CLUSTER_EPS", "0.2"))
DEFAULT_MIN_SAMPLES = int(os.getenv("FACE_CLUSTER_MIN_SAMPLES", "2"))


def normalize(embeddings):
    """L2-normalise each row (zero vectors are left as they are)."""
    embeddings = np.asarray(embeddings, dtype=float)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return embeddings / norms


def centroid(embeddings):
    """Unit-length mean direction of one person's face embeddings."""
    mean = normalize(embeddings).mean(axis=0)
    return mean / (np.linalg.norm(mean) or 1.0)


def plan_assignments(embeddings, centroids, eps, min_samples, match_eps=None):
    """Decide where each not-yet-assigned face goes.

    embeddings: (n, d) raw embeddings of faces that have no person yet.
    centroids:  (p, d) unit centroids of the existing people (p may be 0).

    Step 1 attaches a face to the most similar existing person when the cosine
    similarity is at least 1 - match_eps (match_eps defaults to eps).
    Step 2 clusters the faces left over with DBSCAN (cosine distance, radius eps).

    Returns (matched, labels), both of length n:
      matched[i] is the index into `centroids` of the person face i joins, or -1.
      labels[i] is face i's DBSCAN cluster among the unmatched faces, or -1 for
      faces that were matched in step 1 or are noise.
    """
    vectors = normalize(embeddings)
    matched = np.full(len(vectors), -1, dtype=int)
    labels = np.full(len(vectors), -1, dtype=int)

    centroids = np.asarray(centroids, dtype=float)
    if len(centroids):
        similarity = vectors @ centroids.T
        best = similarity.argmax(axis=1)
        threshold = 1 - (eps if match_eps is None else match_eps)
        matched = np.where(similarity[np.arange(len(vectors)), best] >= threshold, best, -1)

    unmatched = np.flatnonzero(matched == -1)
    if len(unmatched):
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine").fit(vectors[unmatched])
        labels[unmatched] = clustering.labels_

    return matched, labels
