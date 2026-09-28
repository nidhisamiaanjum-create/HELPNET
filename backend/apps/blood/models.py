from django.conf import settings
from django.db import models
import uuid


class BloodGroup(models.TextChoices):
	A_POSITIVE = "A+", "A+"
	A_NEGATIVE = "A-", "A-"
	B_POSITIVE = "B+", "B+"
	B_NEGATIVE = "B-", "B-"
	AB_POSITIVE = "AB+", "AB+"
	AB_NEGATIVE = "AB-", "AB-"
	O_POSITIVE = "O+", "O+"
	O_NEGATIVE = "O-", "O-"


class DonorProfile(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="blood_donor_profile",
	)
	blood_group = models.CharField(max_length=3, choices=BloodGroup.choices)
	area = models.CharField(max_length=120)
	is_available = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.user.full_name} ({self.blood_group}, {self.area})"


class BloodRequest(models.Model):
	class Status(models.TextChoices):
		OPEN = "open", "Open"
		FULFILLED = "fulfilled", "Fulfilled"
		CLOSED = "closed", "Closed"

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	requester = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="blood_requests",
	)
	blood_group = models.CharField(max_length=3, choices=BloodGroup.choices)
	area = models.CharField(max_length=120)
	hospital = models.CharField(max_length=200, blank=True)
	details = models.TextField(blank=True)
	status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"{self.blood_group} request in {self.area} ({self.status})"


class DonationHistory(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	donor = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name="blood_donations",
	)
	blood_request = models.OneToOneField(
		BloodRequest,
		on_delete=models.PROTECT,
		related_name="donation_history",
	)
	donated_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-donated_at"]

	def __str__(self):
		return f"{self.donor.full_name} donated for {self.blood_request_id}"
