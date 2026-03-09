from django.urls import path
from .views import upload_photo, list_photos

urlpatterns = [
    path('upload/', upload_photo, name='upload_photo'),
    path('', list_photos, name='list_photos'),
]