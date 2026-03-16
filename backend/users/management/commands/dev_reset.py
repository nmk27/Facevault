import os
import shutil

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection

from faces.models import Face
from photos.models import Photo


class Command(BaseCommand):
    help = "Reset development database and media files."

    def handle(self, *args, **kwargs):

        self.stdout.write("Deleting database records...")

        Face.objects.all().delete()
        Photo.objects.all().delete()

        self.stdout.write("Resetting database sequences...")

        with connection.cursor() as cursor:

            try:
                cursor.execute("ALTER SEQUENCE photos_photo_id_seq RESTART WITH 1;")
                cursor.execute("ALTER SEQUENCE faces_face_id_seq RESTART WITH 1;")
            except Exception:
                pass

            try:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='photos_photo';")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='faces_face';")
            except Exception:
                pass

        self.stdout.write("Deleting media files...")

        photos_dir = os.path.join(settings.MEDIA_ROOT, "photos")
        faces_dir = os.path.join(settings.MEDIA_ROOT, "faces")

        for directory in [photos_dir, faces_dir]:

            if os.path.exists(directory):
                shutil.rmtree(directory)

            os.makedirs(directory, exist_ok=True)

        self.stdout.write(self.style.SUCCESS("Development reset complete."))