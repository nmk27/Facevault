import io
import shutil
import tempfile
from datetime import datetime, timezone
from unittest import mock

import pillow_heif
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from faces.models import Face

from .models import Photo

TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix='facevault-tests-')
EMBEDDING = [1.0] + [0.0] * 511
EXIF_IFD = 0x8769
DATETIME_ORIGINAL = 0x9003
ORIENTATION = 0x0112


def make_exif(orientation=None, taken='2021:07:14 23:30:00'):
    exif = Image.Exif()
    if orientation:
        exif[ORIENTATION] = orientation
    if taken:
        exif[EXIF_IFD] = {DATETIME_ORIGINAL: taken}
    return exif


def image_bytes(size=(800, 600), fmt='JPEG', mode='RGB', exif=None):
    buffer = io.BytesIO()
    image = Image.new(mode, size, (120, 90, 60, 255)[:len(mode)])
    if fmt == 'HEIF':
        pillow_heif.from_pillow(image).save(
            buffer, quality=80, exif=exif.tobytes() if exif else None)
    else:
        image.save(buffer, format=fmt, exif=exif or Image.Exif())
    return buffer.getvalue()


def upload_file(name='photo.jpg', content_type='image/jpeg', **kwargs):
    return SimpleUploadedFile(name, image_bytes(**kwargs), content_type)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class MediaTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)


class PhotoIngestTests(MediaTestCase):
    def test_dimensions_and_thumbnail_are_persisted(self):
        photo = Photo.objects.create(image=upload_file(size=(800, 600)))

        fresh = Photo.objects.get(pk=photo.pk)
        self.assertEqual((fresh.width, fresh.height), (800, 600))
        self.assertTrue(fresh.thumbnail.name.startswith('thumbnails/thumb_'))
        with Image.open(fresh.thumbnail.path) as thumb:
            self.assertEqual(thumb.format, 'JPEG')
            self.assertLessEqual(max(thumb.size), 300)

    def test_dimensions_follow_exif_orientation(self):
        # Stored sideways (800x600) with Orientation=6: displayed as 600x800 portrait.
        photo = Photo.objects.create(
            image=upload_file(size=(800, 600), exif=make_exif(orientation=6)))

        fresh = Photo.objects.get(pk=photo.pk)
        self.assertEqual((fresh.width, fresh.height), (600, 800))
        with Image.open(fresh.thumbnail.path) as thumb:
            self.assertGreater(thumb.height, thumb.width)

    def test_original_jpeg_bytes_are_left_untouched(self):
        content = image_bytes(exif=make_exif(orientation=6))
        photo = Photo.objects.create(
            image=SimpleUploadedFile('orig.jpg', content, 'image/jpeg'))

        with Photo.objects.get(pk=photo.pk).image.open('rb') as stored:
            self.assertEqual(stored.read(), content)

    def test_heic_is_converted_to_jpeg(self):
        photo = Photo.objects.create(image=upload_file(
            name='iphone.heic', content_type='image/heic', fmt='HEIF', size=(400, 300)))

        fresh = Photo.objects.get(pk=photo.pk)
        self.assertTrue(fresh.image.name.endswith('.jpg'), fresh.image.name)
        with Image.open(fresh.image.path) as stored:
            self.assertEqual(stored.format, 'JPEG')
            self.assertEqual(stored.size, (400, 300))
        self.assertEqual((fresh.width, fresh.height), (400, 300))

    def test_taken_at_is_read_from_exif(self):
        photo = Photo.objects.create(image=upload_file(exif=make_exif()))

        self.assertEqual(
            photo.taken_at, datetime(2021, 7, 14, 23, 30, tzinfo=timezone.utc))

    def test_taken_at_from_heic_exif(self):
        photo = Photo.objects.create(image=upload_file(
            name='iphone.heic', content_type='image/heic', fmt='HEIF', exif=make_exif()))

        self.assertEqual(
            photo.taken_at, datetime(2021, 7, 14, 23, 30, tzinfo=timezone.utc))

    def test_missing_or_invalid_exif_date_gives_none(self):
        no_date = Photo.objects.create(image=upload_file(exif=make_exif(taken=None)))
        zeroed = Photo.objects.create(
            image=upload_file(exif=make_exif(taken='0000:00:00 00:00:00')))

        self.assertIsNone(no_date.taken_at)
        self.assertIsNone(zeroed.taken_at)

    def test_resaving_does_not_regenerate_derived_files(self):
        photo = Photo.objects.create(image=upload_file())
        thumbnail_name = photo.thumbnail.name

        photo.save()

        self.assertEqual(Photo.objects.get(pk=photo.pk).thumbnail.name, thumbnail_name)


@mock.patch('photos.views.generate_embedding', return_value=EMBEDDING)
class UploadEndpointTests(MediaTestCase):
    def upload(self, **kwargs):
        return self.client.post('/photos/upload/', {'image': upload_file(**kwargs)})

    def test_detection_and_crops_use_the_oriented_image(self, _embedding):
        seen = {}

        def fake_detect(image):
            seen['size'] = image.size
            return [{'box': [10, 20, 100, 120], 'confidence': 0.99}]

        with mock.patch('photos.views.detect_faces', side_effect=fake_detect):
            response = self.upload(size=(800, 600), exif=make_exif(orientation=6))

        self.assertEqual(response.status_code, 201)
        self.assertEqual(seen['size'], (600, 800))
        face = Face.objects.get()
        self.assertEqual((face.x, face.y, face.width, face.height), (10, 20, 100, 120))
        with Image.open(face.face_image.path) as crop:
            self.assertEqual(crop.size, (100, 120))

    def test_png_with_transparency_is_accepted(self, _embedding):
        with mock.patch('photos.views.detect_faces', return_value=[
                {'box': [10, 20, 100, 120], 'confidence': 0.99}]):
            response = self.upload(
                name='alpha.png', content_type='image/png', fmt='PNG', mode='RGBA')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Face.objects.count(), 1)

    def test_response_includes_derived_metadata(self, _embedding):
        with mock.patch('photos.views.detect_faces', return_value=[]):
            body = self.upload(size=(800, 600), exif=make_exif()).json()

        self.assertEqual((body['width'], body['height']), (800, 600))
        self.assertEqual(body['taken_at'], '2021-07-14T23:30:00Z')

    def test_client_cannot_set_derived_fields(self, _embedding):
        with mock.patch('photos.views.detect_faces', return_value=[]):
            response = self.client.post('/photos/upload/', {
                'image': upload_file(size=(800, 600), exif=make_exif()),
                'width': 1,
                'height': 1,
                'taken_at': '1999-01-01T00:00:00Z',
            })

        photo = Photo.objects.get(pk=response.json()['id'])
        self.assertEqual((photo.width, photo.height), (800, 600))
        self.assertEqual(photo.taken_at.year, 2021)


class PhotoReadEndpointTests(MediaTestCase):
    def make_photos(self, taken_years):
        # bulk_create skips save(), so no files are written for these list/ordering fixtures.
        Photo.objects.bulk_create([
            Photo(image=f'photos/{i}.jpg',
                  taken_at=datetime(year, 6, 1, tzinfo=timezone.utc) if year else None)
            for i, year in enumerate(taken_years)
        ])

    def test_detail_returns_one_photo(self):
        photo = Photo.objects.create(image=upload_file(size=(800, 600)))

        response = self.client.get(f'/photos/{photo.pk}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], photo.pk)
        self.assertEqual(response.json()['width'], 800)

    def test_detail_404_for_unknown_photo(self):
        self.assertEqual(self.client.get('/photos/99999/').status_code, 404)

    def test_list_pages_hold_24_photos(self):
        self.make_photos([2020] * 30)

        page1 = self.client.get('/photos/').json()
        page2 = self.client.get('/photos/?page=2').json()

        self.assertEqual(page1['count'], 30)
        self.assertEqual(len(page1['results']), 24)
        self.assertEqual(len(page2['results']), 6)
        ids = [p['id'] for p in page1['results'] + page2['results']]
        self.assertEqual(len(set(ids)), 30)

    def test_list_is_ordered_by_capture_date_with_upload_time_fallback(self):
        # Upload order: 2020 shot, undated, 2019 shot. The undated one counts as "now".
        self.make_photos([2020, None, 2019])
        by_index = {p.image.name: p.pk for p in Photo.objects.all()}

        ids = [p['id'] for p in self.client.get('/photos/').json()['results']]

        self.assertEqual(
            ids, [by_index['photos/1.jpg'], by_index['photos/0.jpg'], by_index['photos/2.jpg']])
