from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q
from .models import Face
from photos.models import Photo


@api_view(['GET'])
def get_faces(request, photo_id):
    """Get all faces detected in a specific photo."""
    faces = Face.objects.filter(photo_id=photo_id)

    data = [
        {
            'id': face.id,
            'x': face.x,
            'y': face.y,
            'width': face.width,
            'height': face.height,
            'confidence': face.confidence,
            'person_id': face.person_id,
        }
        for face in faces
    ]

    return Response(data)


@api_view(['GET'])
def list_people(request):
    """List all people (unique person_ids) with face counts."""
    people = (
        Face.objects
        .filter(person_id__isnull=False)
        .exclude(person_id=-1)
        .values('person_id')
        .annotate(face_count=Count('id'))
        .order_by('person_id')
    )

    data = [
        {
            'person_id': int(p['person_id']),
            'face_count': p['face_count'],
        }
        for p in people
    ]

    return Response(data)


@api_view(['GET'])
def get_person_faces(request, person_id):
    """Get all faces belonging to a specific person."""
    faces = Face.objects.filter(person_id=person_id).select_related('photo')

    if not faces.exists():
        return Response(
            {'detail': f'No faces found for person_id={person_id}'},
            status=status.HTTP_404_NOT_FOUND
        )

    data = [
        {
            'id': face.id,
            'person_id': face.person_id,
            'photo_id': face.photo_id,
            'photo': {
                'id': face.photo.id,
                'image': face.photo.image.url if face.photo.image else None,
                'thumbnail': face.photo.thumbnail.url if face.photo.thumbnail else None,
            },
            'x': face.x,
            'y': face.y,
            'width': face.width,
            'height': face.height,
            'confidence': face.confidence,
            'face_image': face.face_image.url if face.face_image else None,
            'created_at': face.created_at.isoformat(),
        }
        for face in faces
    ]

    return Response(data)
