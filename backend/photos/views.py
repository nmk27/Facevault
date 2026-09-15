from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView
import logging

from faces.models import Face
from ml.detect_faces import detect_faces
from ml.cluster_faces import cluster_faces

from .models import Photo
from .serializers import PhotoSerializer

from PIL import Image
import io
from django.core.files.base import ContentFile

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

        # Run face detection after saving the photo
        faces = detect_faces(serializer.instance.image.path)
        image = Image.open(serializer.instance.image.path)

        for face in faces:
            x, y, width, height = face["box"]
            confidence = face["confidence"]

            if confidence < 0.95:
                continue

            x = max(0, x)
            y = max(0, y)
            cropped_face = image.crop((x, y, x + width, y + height))

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
    queryset = Photo.objects.all().order_by('-uploaded_at')
    serializer_class = PhotoSerializer
