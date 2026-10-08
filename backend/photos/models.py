import io
import os

from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageOps

from ml.image_utils import read_taken_at

# Formats every browser can render. Anything else (HEIC from iPhones, TIFF, ...)
# is converted to JPEG on upload.
BROWSER_FORMATS = {'JPEG', 'MPO', 'PNG', 'WEBP', 'GIF'}


class Photo(models.Model):
    image = models.ImageField(upload_to='photos/')
    thumbnail = models.ImageField(
        upload_to='thumbnails/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Camera wall-clock time from EXIF (labelled UTC, see ml.image_utils.read_taken_at).
    taken_at = models.DateTimeField(null=True, blank=True)

    # Pixel size of the image as displayed (EXIF orientation applied); face boxes use the same space.
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)

    THUMBNAIL_SIZE = (300, 300)

    def save(self, *args, **kwargs):
        if self._state.adding and self.image:
            self._ingest_upload()
        super().save(*args, **kwargs)

    def _ingest_upload(self):
        """Derive size, capture date and thumbnail before the row is first written."""
        upload = self.image.file
        upload.seek(0)
        with Image.open(upload) as source:
            source_format = source.format
            self.taken_at = read_taken_at(source)
            oriented = ImageOps.exif_transpose(source).convert('RGB')

        stem = os.path.splitext(os.path.basename(self.image.name))[0]

        if source_format in BROWSER_FORMATS:
            upload.seek(0)  # keep the original bytes untouched
        else:
            self.image.save(
                f'{stem}.jpg', self._jpeg(oriented, quality=92), save=False)

        self.width, self.height = oriented.size

        thumb = oriented.copy()
        thumb.thumbnail(self.THUMBNAIL_SIZE)
        self.thumbnail.save(
            f'thumb_{stem}.jpg', self._jpeg(thumb, quality=85), save=False)

    @staticmethod
    def _jpeg(image, quality):
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=quality)
        return ContentFile(buffer.getvalue())

    def __str__(self):
        return f"Photo {self.id}"
