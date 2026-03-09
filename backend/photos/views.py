from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Photo
from .serializers import PhotoSerializer


@api_view(['POST'])
def upload_photo(request):
    serializer = PhotoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def list_photos(request):
    photos = Photo.objects.all().order_by('-uploaded_at')
    serializer = PhotoSerializer(photos, many=True)
    return Response(serializer.data)
