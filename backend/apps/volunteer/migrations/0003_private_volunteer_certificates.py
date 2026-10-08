from django.core.files import File
from django.core.files.storage import default_storage
from django.db import migrations, models

from apps.volunteer.storage import VolunteerPrivateCertificateStorage


def move_certificates_to_private_storage(apps, schema_editor):
    document_model = apps.get_model("volunteer", "VolunteerProfileDocument")
    private_storage = VolunteerPrivateCertificateStorage()
    for document in document_model.objects.exclude(file="").iterator():
        old_name = document.file.name
        if not default_storage.exists(old_name):
            continue
        with default_storage.open(old_name, "rb") as source:
            private_name = private_storage.save(old_name, File(source))
        document.file.name = private_name
        document.save(update_fields=["file"])
        default_storage.delete(old_name)


def restore_certificates_to_default_storage(apps, schema_editor):
    document_model = apps.get_model("volunteer", "VolunteerProfileDocument")
    private_storage = VolunteerPrivateCertificateStorage()
    for document in document_model.objects.exclude(file="").iterator():
        old_name = document.file.name
        if not private_storage.exists(old_name):
            continue
        with private_storage.open(old_name, "rb") as source:
            default_name = default_storage.save(old_name, File(source))
        document.file.name = default_name
        document.save(update_fields=["file"])
        private_storage.delete(old_name)


class Migration(migrations.Migration):
    dependencies = [("volunteer", "0002_volunteerprofiledocument")]

    operations = [
        migrations.RunPython(move_certificates_to_private_storage, restore_certificates_to_default_storage),
        migrations.AlterField(
            model_name="volunteerprofiledocument",
            name="file",
            field=models.FileField(storage=VolunteerPrivateCertificateStorage(), upload_to="volunteer_certificates/%Y/%m/"),
        ),
    ]