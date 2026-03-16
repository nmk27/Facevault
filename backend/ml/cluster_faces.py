import numpy as np
from sklearn.cluster import DBSCAN
from faces.models import Face


def cluster_faces():

    faces = Face.objects.exclude(embedding=None)

    embeddings = []
    face_ids = []

    for face in faces:
        embeddings.append(face.embedding)
        face_ids.append(face.id)

    embeddings = np.array(embeddings)

    clustering = DBSCAN(eps=0.6, min_samples=2).fit(embeddings)

    labels = clustering.labels_

    for face_id, label in zip(face_ids, labels):
        Face.objects.filter(id=face_id).update(person_id=label)