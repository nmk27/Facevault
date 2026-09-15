import os

import numpy as np
from sklearn.cluster import DBSCAN

from faces.models import Face, Person


DEFAULT_CLUSTER_EPS = float(os.getenv("FACE_CLUSTER_EPS", "0.4"))
DEFAULT_CLUSTER_MIN_SAMPLES = int(os.getenv("FACE_CLUSTER_MIN_SAMPLES", "2"))


def _normalize(embeddings):
    embeddings = np.array(embeddings, dtype=float)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return embeddings / norms


def cluster_faces(eps=DEFAULT_CLUSTER_EPS, min_samples=DEFAULT_CLUSTER_MIN_SAMPLES):
    """Assign unclustered faces to people.

    Faces already linked to a Person keep that identity forever (names survive
    new uploads). Unassigned faces are first matched against existing people
    by embedding similarity; anything left over is clustered among itself and,
    where a cluster of size >= min_samples emerges, turned into new people.
    """
    similarity_threshold = 1 - eps

    unassigned_faces = list(Face.objects.filter(person=None).exclude(embedding=None))

    if not unassigned_faces:
        return {
            "faces_processed": 0,
            "existing_person_matches": 0,
            "new_persons_created": 0,
            "noise_faces": 0,
            "eps": eps,
            "min_samples": min_samples,
        }

    existing_people = list(
        Person.objects.filter(faces__embedding__isnull=False).distinct()
    )
    person_centroids = []
    for person in existing_people:
        member_embeddings = list(person.faces.exclude(embedding=None).values_list("embedding", flat=True))
        if not member_embeddings:
            continue
        centroid = _normalize(member_embeddings).mean(axis=0)
        person_centroids.append((person, centroid / (np.linalg.norm(centroid) or 1.0)))

    still_unassigned = []
    existing_person_matches = 0

    for face in unassigned_faces:
        face_vector = _normalize([face.embedding])[0]

        best_person = None
        best_similarity = -1.0
        for person, centroid in person_centroids:
            similarity = float(np.dot(face_vector, centroid))
            if similarity > best_similarity:
                best_similarity = similarity
                best_person = person

        if best_person is not None and best_similarity >= similarity_threshold:
            Face.objects.filter(id=face.id).update(person=best_person)
            existing_person_matches += 1
        else:
            still_unassigned.append(face)

    new_persons_created = 0
    noise_faces = 0

    if still_unassigned:
        embeddings = _normalize([face.embedding for face in still_unassigned])

        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine").fit(embeddings)
        labels = clustering.labels_

        label_to_person = {}
        for face, label in zip(still_unassigned, labels):
            if label == -1:
                noise_faces += 1
                continue

            if label not in label_to_person:
                label_to_person[label] = Person.objects.create(name="")
                new_persons_created += 1

            Face.objects.filter(id=face.id).update(person=label_to_person[label])

    return {
        "faces_processed": len(unassigned_faces),
        "existing_person_matches": existing_person_matches,
        "new_persons_created": new_persons_created,
        "noise_faces": noise_faces,
        "eps": eps,
        "min_samples": min_samples,
    }
