import os
import shutil
from django.conf import settings
from django.db import connection

from faces.models import Face
from photos.models import Photo


def clear_faces(delete_files=True):
    """
    Delete all Face records.
    Optionally remove cropped face images from media/faces/.
    """

    if delete_files:
        faces_dir = os.path.join(settings.MEDIA_ROOT, "faces")

        if os.path.exists(faces_dir):
            shutil.rmtree(faces_dir)
            os.makedirs(faces_dir, exist_ok=True)

    Face.objects.all().delete()

    print("All face records deleted.")


def clear_embeddings():
    """
    Remove embeddings and clustering labels but keep faces.
    Useful when experimenting with embedding models.
    """

    faces = Face.objects.all()

    for face in faces:
        face.embedding = None
        face.person_id = None
        face.save()

    print("Embeddings and clustering reset.")


def reset_clustering():
    """
    Remove only the person_id labels.
    Useful when re-running clustering.
    """

    faces = Face.objects.all()

    for face in faces:
        face.person_id = None
        face.save()

    print("Clustering labels cleared.")
    
    
def reset_db_sequences():
    """
    Reset auto-increment IDs for Photo and Face tables.
    Works with PostgreSQL and SQLite.
    """

    with connection.cursor() as cursor:

        # PostgreSQL
        try:
            cursor.execute("ALTER SEQUENCE photos_photo_id_seq RESTART WITH 1;")
            cursor.execute("ALTER SEQUENCE faces_face_id_seq RESTART WITH 1;")
        except Exception:
            pass

        # SQLite fallback
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='photos_photo';")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='faces_face';")
        except Exception:
            pass


def clear_everything(delete_files=True):
    """
    Completely reset development data:
    - Deletes Face records
    - Deletes Photo records
    - Removes media/photos and media/faces files
    """

    if delete_files:
        photos_dir = os.path.join(settings.MEDIA_ROOT, "photos")
        faces_dir = os.path.join(settings.MEDIA_ROOT, "faces")

        for directory in [photos_dir, faces_dir]:
            if os.path.exists(directory):
                shutil.rmtree(directory)
                os.makedirs(directory, exist_ok=True)

    Face.objects.all().delete()
    Photo.objects.all().delete()
    
    reset_db_sequences()

    print("Database and media files cleared.")


def face_count():
    """
    Quick debugging helper.
    """

    print("Faces in database:", Face.objects.count())


def photo_count():
    """
    Quick debugging helper.
    """

    print("Photos in database:", Photo.objects.count())
    
    
    
if __name__ == "__main__":
    # Example usage:
    clear_everything()