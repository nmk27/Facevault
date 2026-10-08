import numpy as np

from faces.models import Face, Person
from ml.clustering import DEFAULT_EPS, DEFAULT_MIN_SAMPLES, centroid, plan_assignments


DEFAULT_CLUSTER_EPS = DEFAULT_EPS
DEFAULT_CLUSTER_MIN_SAMPLES = DEFAULT_MIN_SAMPLES


def cluster_faces(eps=DEFAULT_CLUSTER_EPS, min_samples=DEFAULT_CLUSTER_MIN_SAMPLES):
    """Assign unclustered faces to people.

    Faces already linked to a Person keep that identity forever (names survive
    new uploads). Unassigned faces are first matched against existing people
    by embedding similarity; anything left over is clustered among itself and,
    where a cluster of size >= min_samples emerges, turned into new people.

    The decisions come from ml.clustering.plan_assignments; this function only
    reads the faces from, and writes the result to, the database.
    """
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
    people = []
    centroids = []
    for person in existing_people:
        member_embeddings = list(person.faces.exclude(embedding=None).values_list("embedding", flat=True))
        if not member_embeddings:
            continue
        people.append(person)
        centroids.append(centroid(member_embeddings))

    matched, labels = plan_assignments(
        [face.embedding for face in unassigned_faces],
        np.array(centroids),
        eps,
        min_samples,
    )

    existing_person_matches = 0
    new_persons_created = 0
    noise_faces = 0
    label_to_person = {}

    for face, person_index, label in zip(unassigned_faces, matched, labels):
        if person_index >= 0:
            Face.objects.filter(id=face.id).update(person=people[person_index])
            existing_person_matches += 1
            continue

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
