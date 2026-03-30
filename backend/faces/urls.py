from django.urls import path
from .views import get_faces, list_people, get_person_faces

urlpatterns = [
    path('<int:photo_id>/', get_faces, name='get_faces'),
    path('people/', list_people, name='list_people'),
    path('people/<int:person_id>/', get_person_faces, name='get_person_faces'),
]