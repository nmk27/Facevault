import os
import numpy as np
from sklearn.cluster import DBSCAN
from faces.models import Face


DEFAULT_CLUSTER_EPS = float(os.getenv("FACE_CLUSTER_EPS", "0.4"))
DEFAULT_CLUSTER_MIN_SAMPLES = int(os.getenv("FACE_CLUSTER_MIN_SAMPLES", "2"))


def cluster_faces(eps=DEFAULT_CLUSTER_EPS, min_samples=DEFAULT_CLUSTER_MIN_SAMPLES):
    faces = Face.objects.exclude(embedding=None)

    embeddings = []
    face_ids = []

    for face in faces:
        embeddings.append(face.embedding)
        face_ids.append(face.id)

    if not embeddings:
        return {
            "faces_processed": 0,
            "clusters_assigned": 0,
            "noise_faces": 0,
            "eps": eps,
            "min_samples": min_samples,
        }

    embeddings = np.array(embeddings, dtype=float)

    # FaceNet embeddings are best clustered using cosine distance.
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms

    clustering = DBSCAN(eps=eps, min_samples=min_samples,
                        metric="cosine").fit(embeddings)
    labels = clustering.labels_

    for face_id, label in zip(face_ids, labels):
        Face.objects.filter(id=face_id).update(person_id=int(label))

    unique_clusters = {int(label) for label in labels if int(label) >= 0}
    noise_faces = int((labels == -1).sum())
    return {
        "faces_processed": len(face_ids),
        "clusters_assigned": len(unique_clusters),
        "noise_faces": noise_faces,
        "eps": eps,
        "min_samples": min_samples,
    }
