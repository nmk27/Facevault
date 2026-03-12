from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView

from faces.models import Face
from faces.models import Face
from ml.detect_faces import detect_faces

from .models import Photo
from .serializers import PhotoSerializer


@api_view(['POST'])
def upload_photo(request):
    serializer = PhotoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()

        # Run face detection after saving the photo
        faces = detect_faces(serializer.instance.image.path)

        for face in faces:
            x, y, width, height = face["box"]
            confidence = face["confidence"]

            if confidence < 0.95:
                continue

            Face.objects.create(
                photo=serializer.instance,
                x=x,
                y=y,
                width=width,
                height=height,
                confidence=confidence,
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
