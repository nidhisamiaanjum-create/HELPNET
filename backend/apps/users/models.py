from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
import uuid


class CustomUserManager(UserManager):
    def _create_user(self, phone_number, email, full_name, password, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required")

        if not email:
            raise ValueError("Email is required")

        if not full_name:
            raise ValueError("Full name is required")

        email = self.normalize_email(email)

        user = self.model(
            phone_number=phone_number,
            email=email,
            full_name=full_name,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, phone_number, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(
            phone_number,
            email,
            full_name,
            password,
            **extra_fields
        )

    def create_superuser(self, phone_number, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(
            phone_number,
            email,
            full_name,
            password,
            **extra_fields
        )


class User(AbstractUser):

    class Role(models.TextChoices):
        CITIZEN = "Citizen", "Citizen"
        NGO = "NGO", "NGO"
        VOLUNTEER = "Volunteer", "Volunteer"
        FARMER = "Farmer", "Farmer"
        BLOOD_DONOR = "Blood Donor", "Blood Donor"
        ADMIN = "Admin", "Admin"

    user_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    username = None

    full_name = models.CharField(max_length=150)

    email = models.EmailField(unique=True)

    phone_number = models.CharField(
        max_length=20,
        unique=True
    )

    # Retained for compatibility with existing integrations and data. New
    # accounts leave this blank; permissions are based on owned profiles.
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        blank=True,
        default="",
    )
    active_profile = models.ForeignKey(
        "UserProfile", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="active_for_users",
    )

    location = models.CharField(
        max_length=255,
        blank=True
    )

    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True,
    )

    bio = models.TextField(blank=True)

    date_of_birth = models.DateField(blank=True, null=True)

    class Gender(models.TextChoices):
        FEMALE = "female", "Female"
        MALE = "male", "Male"
        OTHER = "other", "Other"
        PREFER_NOT_TO_SAY = "not_specified", "Prefer not to say"

    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        blank=True,
    )

    # Personal information is private until the account holder opts in.
    is_phone_visible = models.BooleanField(default=False)
    is_email_visible = models.BooleanField(default=False)
    is_location_visible = models.BooleanField(default=False)
    is_date_of_birth_visible = models.BooleanField(default=False)

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "phone_number"

    REQUIRED_FIELDS = ["email", "full_name"]

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"


class UserProfile(models.Model):
    class Type(models.TextChoices):
        CITIZEN = "citizen", "Citizen"
        VOLUNTEER = "volunteer", "Volunteer"
        FARMER = "farmer", "Farmer"
        NGO = "ngo", "NGO"
        BLOOD_DONOR = "blood_donor", "Blood Donor"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
    class NGOApprovalStatus(models.TextChoices):
        NOT_REQUIRED = "not_required", "Not Required"
        PENDING = "pending", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profiles")
    profile_type = models.CharField(max_length=20, choices=Type.choices)
    display_name = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    ngo_approval_status = models.CharField(
        max_length=20,
        choices=NGOApprovalStatus.choices,
        default=NGOApprovalStatus.NOT_REQUIRED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("user", "profile_type"), name="uniq_user_profile_type")]

    def __str__(self):
        return f"{self.get_profile_type_display()} profile for {self.user}"
