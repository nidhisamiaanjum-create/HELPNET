from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("volunteer", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="VolunteerProfileDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="volunteer_certificates/%Y/%m/")),
                ("original_name", models.CharField(max_length=255)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents", to="volunteer.volunteerprofile")),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
    ]
