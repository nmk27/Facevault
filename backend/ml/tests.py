from unittest import mock

import numpy as np
import torch
from django.test import TestCase
from PIL import Image

from evaluation.simulate import simulate_uploads
from faces.models import Face, Person
from ml.cluster_faces import cluster_faces
from ml.clustering import DEFAULT_EPS, DEFAULT_MIN_SAMPLES, centroid, normalize, plan_assignments
from ml.generate_embeddings import generate_embedding
from photos.models import Photo

DIM = 64


def unit(rng):
    v = rng.standard_normal(DIM)
    return v / np.linalg.norm(v)


def near(direction, rng, sigma=0.03):
    return direction + sigma * rng.standard_normal(DIM)


class PlanAssignmentsTests(TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(0)
        self.alice, self.bob = unit(self.rng), unit(self.rng)

    def test_face_close_to_a_person_joins_them(self):
        matched, labels = plan_assignments(
            [near(self.alice, self.rng)], np.array([self.alice, self.bob]), eps=0.4, min_samples=2)

        self.assertEqual(matched.tolist(), [0])
        self.assertEqual(labels.tolist(), [-1])

    def test_matching_picks_the_most_similar_person(self):
        matched, _ = plan_assignments(
            [near(self.bob, self.rng)], np.array([self.alice, self.bob]), eps=0.9, min_samples=2)

        self.assertEqual(matched.tolist(), [1])

    def test_unmatched_faces_cluster_into_new_people_and_singletons_are_noise(self):
        carol, dave = unit(self.rng), unit(self.rng)
        faces = [near(carol, self.rng), near(carol, self.rng), near(dave, self.rng)]

        matched, labels = plan_assignments(faces, np.array([self.alice]), eps=0.4, min_samples=2)

        self.assertEqual(matched.tolist(), [-1, -1, -1])
        self.assertEqual(labels[0], labels[1])
        self.assertGreaterEqual(labels[0], 0)
        self.assertEqual(labels[2], -1)  # lone face: DBSCAN noise

    def test_no_existing_people_skips_matching(self):
        matched, labels = plan_assignments(
            [near(self.alice, self.rng), near(self.alice, self.rng)], np.empty((0, DIM)), eps=0.4, min_samples=2)

        self.assertEqual(matched.tolist(), [-1, -1])
        self.assertEqual(labels[0], labels[1])

    def test_match_eps_can_differ_from_the_clustering_eps(self):
        # A face at cosine similarity exactly 0.8 (distance 0.2) from Alice.
        face = 0.8 * self.alice + 0.6 * self._orthogonal(self.alice)
        strict, _ = plan_assignments([face], np.array([self.alice]), eps=0.4, min_samples=2, match_eps=0.1)
        default, _ = plan_assignments([face], np.array([self.alice]), eps=0.4, min_samples=2)

        self.assertEqual(strict.tolist(), [-1])
        self.assertEqual(default.tolist(), [0])

    def _orthogonal(self, v):
        w = unit(self.rng)
        w -= w.dot(v) * v
        return w / np.linalg.norm(w)

    def test_centroid_is_unit_length(self):
        self.assertAlmostEqual(np.linalg.norm(centroid([self.alice * 3, near(self.alice, self.rng)])), 1.0)
        self.assertAlmostEqual(np.linalg.norm(normalize([[3.0, 4.0]])[0]), 1.0)


class ClusterFacesDatabaseTests(TestCase):
    def setUp(self):
        self.photo = Photo.objects.bulk_create([Photo(image='photos/x.jpg')])[0]
        self.rng = np.random.default_rng(1)

    def add_faces(self, embeddings):
        return Face.objects.bulk_create([
            Face(photo=self.photo, x=0, y=0, width=1, height=1, confidence=1.0, embedding=e.tolist())
            for e in embeddings
        ])

    def test_later_uploads_join_existing_people_and_keep_their_names(self):
        alice = unit(self.rng)
        self.add_faces([near(alice, self.rng), near(alice, self.rng)])
        cluster_faces()
        person = Person.objects.get()
        person.name = 'Alice'
        person.save()

        self.add_faces([near(alice, self.rng)])
        stats = cluster_faces()

        self.assertEqual(Person.objects.count(), 1)
        self.assertEqual(Person.objects.get().name, 'Alice')
        self.assertEqual(person.faces.count(), 3)
        self.assertEqual(stats['existing_person_matches'], 1)
        self.assertEqual(stats['new_persons_created'], 0)

    def test_a_lone_face_stays_unassigned_until_a_second_one_arrives(self):
        bob = unit(self.rng)
        self.add_faces([near(bob, self.rng)])
        self.assertEqual(cluster_faces()['noise_faces'], 1)
        self.assertEqual(Person.objects.count(), 0)

        self.add_faces([near(bob, self.rng)])
        stats = cluster_faces()

        self.assertEqual(stats['new_persons_created'], 1)
        self.assertEqual(Face.objects.filter(person=None).count(), 0)

    def test_nothing_to_do_returns_zero_stats(self):
        self.assertEqual(cluster_faces()['faces_processed'], 0)

    def test_evaluation_simulation_matches_the_app(self):
        """evaluation.simulate_uploads must replay cluster_faces() exactly."""
        centers = [unit(self.rng) for _ in range(8)]
        embeddings = np.array([near(c, self.rng, 0.06) for c in centers for _ in range(4)])
        order = self.rng.permutation(len(embeddings))

        for batch_size in (1, 5):
            Face.objects.all().delete()
            Person.objects.all().delete()
            ids_in_upload_order = []
            for start in range(0, len(order), batch_size):
                batch = order[start:start + batch_size]
                ids_in_upload_order += [f.pk for f in self.add_faces(embeddings[batch])]
                cluster_faces()
            app = {pk: person for pk, person in Face.objects.values_list('pk', 'person_id')}
            app_labels = np.empty(len(order), dtype=int)
            app_labels[order] = [app[pk] if app[pk] is not None else -1 for pk in ids_in_upload_order]

            replay, _ = simulate_uploads(
                embeddings, order, eps=DEFAULT_EPS, min_samples=DEFAULT_MIN_SAMPLES, batch_size=batch_size)

            self.assertEqual(self.partition(app_labels), self.partition(replay), f'batch_size={batch_size}')
            self.assertGreater(len(self.partition(replay)), 1)  # not a vacuous comparison

    @staticmethod
    def partition(labels):
        groups = {}
        for index, label in enumerate(labels.tolist()):
            if label != -1:
                groups.setdefault(label, set()).add(index)
        return sorted(sorted(group) for group in groups.values())


class EmbeddingScalingTests(TestCase):
    """The app must feed FaceNet the scaling the evaluation chose (ml/defaults.py)."""

    class RecordingModel:
        def __call__(self, tensor):
            self.seen = tensor
            return torch.zeros(1, 512)

    def seen_range(self, **kwargs):
        model = self.RecordingModel()
        white = Image.new("RGB", (40, 40), (255, 255, 255))
        black = Image.new("RGB", (40, 40), (0, 0, 0))
        with mock.patch("ml.generate_embeddings._model", return_value=model):
            generate_embedding(white, **kwargs)
            high = model.seen.max().item()
            generate_embedding(black, **kwargs)
            low = model.seen.min().item()
        return low, high

    def test_default_is_facenets_own_input_scaling(self):
        low, high = self.seen_range()
        self.assertAlmostEqual(low, -127.5 / 128)
        self.assertAlmostEqual(high, 127.5 / 128)

    def test_the_original_scaling_is_still_available(self):
        self.assertEqual(self.seen_range(standardize=False), (0.0, 1.0))
