from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
import logging

from faces.models import Face
from ml.detect_faces import MIN_FACE_CONFIDENCE, detect_faces
from ml.cluster_faces import cluster_faces
from ml.image_utils import crop_face, open_oriented

from .models import Photo
from .serializers import PhotoSerializer

import io
from django.core.files.base import ContentFile
from django.db.models.functions import Coalesce

from ml.generate_embeddings import generate_embedding


logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif'}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


@api_view(['POST'])
def upload_photo(request):
    uploaded_file = request.FILES.get('image')
    if uploaded_file is not None:
        if uploaded_file.content_type not in ALLOWED_CONTENT_TYPES:
            return Response(
                {'detail': f'Unsupported file type: {uploaded_file.content_type}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if uploaded_file.size > MAX_UPLOAD_SIZE:
            return Response(
                {'detail': 'File exceeds the 10MB upload limit'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    serializer = PhotoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()

        # Detect and crop on the oriented image so boxes match what the browser displays.
        image = open_oriented(serializer.instance.image.path)
        faces = detect_faces(image)

        for face in faces:
            x, y, width, height = face["box"]
            confidence = face["confidence"]

            if confidence < MIN_FACE_CONFIDENCE:
                continue

            x, y, cropped_face = crop_face(image, (x, y, width, height))

            buffer = io.BytesIO()
            cropped_face.save(buffer, format='JPEG')
            face_file = ContentFile(
                buffer.getvalue(), name=f'face_{serializer.instance.id}_{x}_{y}.jpg')

            embedding = generate_embedding(cropped_face)

            Face.objects.create(
                photo=serializer.instance,
                x=x,
                y=y,
                width=width,
                height=height,
                confidence=confidence,
                face_image=face_file,
                embedding=embedding,
            )

        # Keep person identities up to date for all newly embedded faces.
        try:
            cluster_faces()
        except Exception:
            logger.exception("Face clustering failed after upload")

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PhotoListView(ListAPIView):
    # Newest capture date first; photos without an EXIF date fall back to upload time.
    queryset = Photo.objects.annotate(
        sort_date=Coalesce('taken_at', 'uploaded_at')
    ).order_by('-sort_date', '-id')
    serializer_class = PhotoSerializer


class PhotoDetailView(RetrieveAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
