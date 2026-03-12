from django.db import models
from photos.models import Photo


class Face(models.Model):
    photo = models.ForeignKey(
        Photo, on_delete=models.CASCADE, related_name='faces')

    x = models.IntegerField()
    y = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()

    confidence = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Face in photo {self.photo.id}"
