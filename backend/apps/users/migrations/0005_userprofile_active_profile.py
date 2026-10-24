import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


ROLE_MAP = {
    "Citizen": "citizen", "Volunteer": "volunteer", "Farmer": "farmer",
    "NGO": "ngo", "Blood Donor": "blood_donor",
}


def migrate_existing_roles(apps, schema_editor):
    User = apps.get_model("users", "User")
    Profile = apps.get_model("users", "UserProfile")
    existing_role_users = set()
    for user in User.objects.exclude(role="").iterator():
        profile_type = ROLE_MAP.get(user.role)
        if not profile_type:
            if user.role == "Admin":
                # The legacy system treated this persisted role as admin authority.
                # Move that authority to Django's trusted staff flag.
                User.objects.filter(user_id=user.user_id).update(is_staff=True)
            continue
        existing_role_users.add(user.user_id)
        profile, _ = Profile.objects.get_or_create(
            user_id=user.user_id, profile_type=profile_type,
            defaults={"display_name": user.full_name, "status": "active"},
        )
        User.objects.filter(user_id=user.user_id).update(active_profile_id=profile.pk)

    # Existing role data remains attached to User. Ensure older volunteer and
    # donor records with a stale/missing User.role also gain the matching card.
    for app_label, model_name, profile_type in (
        ("volunteer", "VolunteerProfile", "volunteer"),
        ("blood", "DonorProfile", "blood_donor"),
    ):
        RelatedProfile = apps.get_model(app_label, model_name)
        for record in RelatedProfile.objects.select_related("user").iterator():
            profile, _ = Profile.objects.get_or_create(
                user_id=record.user_id,
                profile_type=profile_type,
                defaults={"display_name": record.user.full_name, "status": "active"},
            )
            if record.user_id not in existing_role_users:
                User.objects.filter(user_id=record.user_id, active_profile_id__isnull=True).update(active_profile_id=profile.pk)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_alter_user_role"),
        ("volunteer", "0003_private_volunteer_certificates"),
        ("blood", "0003_bloodrequest_supporting_document"),
    ]
    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("profile_type", models.CharField(choices=[("citizen", "Citizen"), ("volunteer", "Volunteer"), ("farmer", "Farmer"), ("ngo", "NGO"), ("blood_donor", "Blood Donor")], max_length=20)),
                ("display_name", models.CharField(blank=True, max_length=150)),
                ("status", models.CharField(choices=[("active", "Active"), ("inactive", "Inactive")], default="active", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="profiles", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(model_name="userprofile", constraint=models.UniqueConstraint(fields=("user", "profile_type"), name="uniq_user_profile_type")),
        migrations.AddField(model_name="user", name="active_profile", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="active_for_users", to="users.userprofile")),
        migrations.AlterField(model_name="user", name="role", field=models.CharField(blank=True, choices=[("Citizen", "Citizen"), ("NGO", "NGO"), ("Volunteer", "Volunteer"), ("Farmer", "Farmer"), ("Blood Donor", "Blood Donor"), ("Admin", "Admin")], default="", max_length=20)),
        migrations.RunPython(migrate_existing_roles, migrations.RunPython.noop),
    ]
