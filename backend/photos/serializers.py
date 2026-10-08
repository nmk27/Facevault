from rest_framework import serializers
from .models import Photo

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'image', 'thumbnail', 'width', 'height', 'taken_at', 'uploaded_at']
        # Everything except the file itself is derived server-side on upload.
        read_only_fields = ['thumbnail', 'width', 'height', 'taken_at', 'uploaded_at']
