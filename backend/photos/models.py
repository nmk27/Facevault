from django.db import models
from PIL import Image, ImageOps
import os



class Photo(models.Model):
    image = models.ImageField(upload_to='photos/')
    thumbnail = models.ImageField(
        upload_to='thumbnails/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            img = Image.open(self.image.path)
            img = ImageOps.exif_transpose(img)  # Handle EXIF orientation

            img.thumbnail((300, 300))

            thumb_path = os.path.join(
                os.path.dirname(self.image.path),
                'thumb_' + os.path.basename(self.image.path)
            )

            img.save(thumb_path)

            self.thumbnail = 'photos/thumb_' + \
                os.path.basename(self.image.name)
            super().save(update_fields=['thumbnail'])

    def __str__(self):
        return f"Photo {self.id}"
