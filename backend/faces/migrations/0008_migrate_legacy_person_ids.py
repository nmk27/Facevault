from django.db import migrations


def migrate_legacy_ids_forward(apps, schema_editor):
    Face = apps.get_model('faces', 'Face')
    Person = apps.get_model('faces', 'Person')

    legacy_ids = (
        Face.objects.exclude(legacy_person_id=None)
        .exclude(legacy_person_id=-1)
        .values_list('legacy_person_id', flat=True)
        .distinct()
    )

    for legacy_id in legacy_ids:
        person = Person.objects.create(name='')
        Face.objects.filter(legacy_person_id=legacy_id).update(person=person)


def migrate_legacy_ids_backward(apps, schema_editor):
    Face = apps.get_model('faces', 'Face')

    for face in Face.objects.exclude(person=None).select_related('person'):
        # Best-effort reverse: reuse the Person's primary key as the legacy label.
        Face.objects.filter(pk=face.pk).update(legacy_person_id=face.person_id)


class Migration(migrations.Migration):

    dependencies = [
        ('faces', '0007_person_face_person'),
    ]

    operations = [
        migrations.RunPython(migrate_legacy_ids_forward, migrate_legacy_ids_backward),
    ]
