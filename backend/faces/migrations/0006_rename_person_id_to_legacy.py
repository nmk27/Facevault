from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('faces', '0005_face_person_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='face',
            old_name='person_id',
            new_name='legacy_person_id',
        ),
    ]
