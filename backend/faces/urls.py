from django.urls import path
from .views import get_faces

urlpatterns = [
    path('<int:photo_id>/', get_faces, name='get_faces'),
]