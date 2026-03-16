from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView

from faces.models import Face
from faces.models import Face
from ml.detect_faces import detect_faces

from .models import Photo
from .serializers import PhotoSerializer

from PIL import Image
import io
from django.core.files.base import ContentFile

from ml.generate_embeddings import generate_embedding


@api_view(['POST'])
def upload_photo(request):
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
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['GET'])
# def list_photos(request):
#     photos = Photo.objects.all().order_by('-uploaded_at')
#     serializer = PhotoSerializer(photos, many=True)
#     return Response(serializer.data)

class PhotoListView(ListAPIView):
    queryset = Photo.objects.all().order_by('-uploaded_at')
    serializer_class = PhotoSerializer
