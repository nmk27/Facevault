from django.urls import path
from .views import upload_photo, PhotoListView

urlpatterns = [
    path('upload/', upload_photo, name='upload_photo'),
    # path('', list_photos, name='list_photos'),
    path('', PhotoListView.as_view(), name='list_photos'),
]