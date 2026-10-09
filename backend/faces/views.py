from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from django.shortcuts import get_object_or_404
from .models import Face, Person


def _person_summary(person):
    return {
        'id': person.id,
        'name': person.name or f'Person {person.id}',
        'face_count': person.face_count,
    }


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
    """List all identified people with face counts."""
    people = Person.objects.annotate(face_count=Count('faces')).filter(face_count__gt=0).order_by('id')
    return Response([_person_summary(person) for person in people])


@api_view(['GET', 'PATCH'])
def get_person_faces(request, person_id):
    """Get all faces belonging to a specific person, or rename them."""
    person = get_object_or_404(
        Person.objects.annotate(face_count=Count('faces')), pk=person_id
    )

    if request.method == 'PATCH':
        name = request.data.get('name', '')
        if not isinstance(name, str) or not name.strip():
            return Response({'detail': 'name must be a non-empty string'}, status=status.HTTP_400_BAD_REQUEST)
        if len(name) > 100:
            return Response({'detail': 'name must be 100 characters or fewer'}, status=status.HTTP_400_BAD_REQUEST)

        person.name = name.strip()
        person.save(update_fields=['name', 'updated_at'])
        return Response(_person_summary(person))

    faces = Face.objects.filter(person_id=person_id).select_related('photo')

    faces_data = [
        {
            'id': face.id,
            'person_id': face.person_id,
            'photo_id': face.photo_id,
            'photo': {
                'id': face.photo.id,
                'image': face.photo.image.url if face.photo.image else None,
                'thumbnail': face.photo.thumbnail.url if face.photo.thumbnail else None,
                'taken_at': face.photo.taken_at.isoformat() if face.photo.taken_at else None,
                'uploaded_at': face.photo.uploaded_at.isoformat(),
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

    return Response({'person': _person_summary(person), 'faces': faces_data})
