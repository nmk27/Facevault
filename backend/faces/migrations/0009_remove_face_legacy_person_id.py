from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('faces', '0008_migrate_legacy_person_ids'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='face',
            name='legacy_person_id',
        ),
    ]
