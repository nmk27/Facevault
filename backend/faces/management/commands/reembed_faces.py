from django.core.management.base import BaseCommand
from PIL import Image

from faces.models import Face
from ml.generate_embeddings import generate_embedding


class Command(BaseCommand):
    help = (
        "Recompute every face's embedding from its saved crop with the current embedding settings "
        "(ml/defaults.py). People and their names are kept. Run it after changing the embedding "
        "scaling: old and new embeddings must not be mixed."
    )

    def handle(self, *args, **options):
        faces = Face.objects.exclude(face_image="").exclude(face_image=None)
        total = faces.count()
        updated = cleared = 0

        for number, face in enumerate(faces.iterator(), start=1):
            try:
                with face.face_image.open("rb") as handle:
                    crop = Image.open(handle)
                    crop.load()
                embedding = generate_embedding(crop)
            except (OSError, ValueError) as error:
                # A stale embedding would be matched on the wrong scale; leave the face out of clustering.
                Face.objects.filter(pk=face.pk).update(embedding=None)
                cleared += 1
                self.stderr.write(f"face {face.pk}: could not read its crop ({error}); embedding cleared")
                continue
            Face.objects.filter(pk=face.pk).update(embedding=embedding)
            updated += 1
            if number % 100 == 0:
                self.stdout.write(f"  {number}/{total}")

        self.stdout.write(self.style.SUCCESS(f"Re-embedded {updated} faces ({cleared} cleared, {total} with a saved crop)."))
