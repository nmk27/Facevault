from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Face


@api_view(['GET'])
def get_faces(reques, photo_id):
    faces = Face.objects.filter(photo_id=photo_id)

    data = [
        {
            'x': face.x,
            'y': face.y,
            'width': face.width,
            'height': face.height,
            'confidence': face.confidence
        }
        for face in faces
    ]

    return Response(data)
