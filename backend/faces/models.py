from django.db import models
from photos.models import Photo


class Person(models.Model):
    name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or f"Person {self.id}"


class Face(models.Model):
    photo = models.ForeignKey(
        Photo, on_delete=models.CASCADE, related_name='faces')

    x = models.IntegerField()
    y = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()

    confidence = models.FloatField()

    face_image = models.ImageField(upload_to='faces/', null=True, blank=True)
    embedding = models.JSONField(null=True, blank=True)
    person = models.ForeignKey(
        Person, null=True, blank=True, on_delete=models.SET_NULL, related_name='faces')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Face in photo {self.photo.id}"
