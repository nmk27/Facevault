import io
import os
import shutil
import tempfile
from datetime import datetime, timezone
from unittest import mock

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from photos.models import Photo

from .models import Face, Person


class PersonEndpointTests(TestCase):
    def test_person_photos_include_capture_and_upload_dates(self):
        # bulk_create skips Photo.save(), so no image files are needed for this fixture.
        Photo.objects.bulk_create([
            Photo(image='photos/a.jpg', taken_at=datetime(2021, 7, 14, 23, 30, tzinfo=timezone.utc)),
            Photo(image='photos/b.jpg'),
        ])
        dated, undated = Photo.objects.order_by('id')
        person = Person.objects.create(name='Ada')
        for photo in (dated, undated):
            Face.objects.create(
                photo=photo, person=person, x=0, y=0, width=10, height=10, confidence=0.99)

        faces = self.client.get(f'/faces/people/{person.pk}/').json()['faces']

        by_photo = {face['photo_id']: face['photo'] for face in faces}
        self.assertEqual(by_photo[dated.pk]['taken_at'], '2021-07-14T23:30:00+00:00')
        self.assertIsNone(by_photo[undated.pk]['taken_at'])
        self.assertTrue(by_photo[undated.pk]['uploaded_at'])


TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix="facevault-reembed-tests-")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ReembedFacesCommandTests(TestCase):
    NEW_EMBEDDING = [0.25] * 512

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.photo = Photo.objects.bulk_create([Photo(image="photos/x.jpg")])[0]
        self.person = Person.objects.create(name="Ada")

    def make_face(self, with_crop=True, embedding=None):
        face = Face.objects.create(photo=self.photo, person=self.person, x=0, y=0, width=8, height=8,
                                   confidence=0.99, embedding=embedding or [1.0] * 512)
        if with_crop:
            buffer = io.BytesIO()
            Image.new("RGB", (8, 8), (200, 100, 50)).save(buffer, "JPEG")
            face.face_image.save("crop.jpg", ContentFile(buffer.getvalue()), save=True)
        return face

    def run_command(self):
        with mock.patch("faces.management.commands.reembed_faces.generate_embedding",
                        return_value=self.NEW_EMBEDDING) as embed:
            call_command("reembed_faces", stdout=io.StringIO(), stderr=io.StringIO())
        return embed

    def test_embeddings_are_recomputed_from_the_saved_crops_and_people_are_kept(self):
        face = self.make_face()

        embed = self.run_command()

        face.refresh_from_db()
        self.assertEqual(face.embedding, self.NEW_EMBEDDING)
        self.assertEqual(face.person, self.person)
        self.assertEqual(embed.call_count, 1)
        self.assertEqual(embed.call_args.args[0].size, (8, 8))

    def test_faces_without_a_saved_crop_are_left_alone(self):
        face = self.make_face(with_crop=False, embedding=[2.0] * 512)

        embed = self.run_command()

        face.refresh_from_db()
        self.assertEqual(face.embedding, [2.0] * 512)
        self.assertEqual(embed.call_count, 0)

    def test_an_unreadable_crop_clears_the_embedding_instead_of_leaving_a_stale_one(self):
        face = self.make_face()
        os.remove(face.face_image.path)

        self.run_command()

        face.refresh_from_db()
        self.assertIsNone(face.embedding)
        self.assertEqual(face.person, self.person)
