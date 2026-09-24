from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BloodGroup, BloodRequest, DonationHistory, DonorProfile


User = get_user_model()


def profile_data(profile):
	return {
		"user_id": str(profile.user.user_id),
		"full_name": profile.user.full_name,
		"blood_group": profile.blood_group,
		"area": profile.area,
		"is_available": profile.is_available,
	}


def request_data(blood_request):
	return {
		"id": str(blood_request.id),
		"requester_id": str(blood_request.requester.user_id),
		"requester_name": blood_request.requester.full_name,
		"blood_group": blood_request.blood_group,
		"area": blood_request.area,
		"hospital": blood_request.hospital,
		"details": blood_request.details,
		"status": blood_request.status,
		"created_at": blood_request.created_at,
	}


class DonorProfileView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		profile = get_object_or_404(DonorProfile, user=request.user)
		return Response({"success": True, "data": profile_data(profile), "message": "Donor profile loaded."})

	def put(self, request):
		blood_group = request.data.get("blood_group")
		area = str(request.data.get("area", "")).strip()
		is_available = request.data.get("is_available", True)

		if blood_group not in BloodGroup.values:
			return Response(
				{"success": False, "data": None, "message": "Select a valid blood group."},
				status=status.HTTP_400_BAD_REQUEST,
			)
		if not area:
			return Response(
				{"success": False, "data": None, "message": "Area is required."},
				status=status.HTTP_400_BAD_REQUEST,
			)
		if not isinstance(is_available, bool):
			return Response(
				{"success": False, "data": None, "message": "is_available must be true or false."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		profile, _ = DonorProfile.objects.update_or_create(
			user=request.user,
			defaults={
				"blood_group": blood_group,
				"area": area,
				"is_available": is_available,
			},
		)
		return Response({"success": True, "data": profile_data(profile), "message": "Donor profile saved."})


class BloodRequestListCreateView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		requests = BloodRequest.objects.filter(status=BloodRequest.Status.OPEN).select_related("requester")
		return Response({"success": True, "data": [request_data(item) for item in requests], "message": "Open requests loaded."})

	def post(self, request):
		blood_group = request.data.get("blood_group")
		area = str(request.data.get("area", "")).strip()
		if blood_group not in BloodGroup.values:
			return Response(
				{"success": False, "data": None, "message": "Select a valid blood group."},
				status=status.HTTP_400_BAD_REQUEST,
			)
		if not area:
			return Response(
				{"success": False, "data": None, "message": "Area is required."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		blood_request = BloodRequest.objects.create(
			requester=request.user,
			blood_group=blood_group,
			area=area,
			hospital=str(request.data.get("hospital", "")).strip(),
			details=str(request.data.get("details", "")).strip(),
		)
		return Response(
			{"success": True, "data": request_data(blood_request), "message": "Blood request created."},
			status=status.HTTP_201_CREATED,
		)


class BloodRequestMatchesView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request, request_id):
		blood_request = get_object_or_404(BloodRequest, id=request_id)
		profiles = DonorProfile.objects.filter(
			blood_group=blood_request.blood_group,
			area=blood_request.area,
			is_available=True,
		).exclude(user=blood_request.requester).select_related("user")
		data = [profile_data(profile) for profile in profiles]
		return Response({"success": True, "data": data, "message": "Matching donors loaded."})


class BloodRequestCompleteView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request, request_id):
		blood_request = get_object_or_404(
			BloodRequest.objects.select_related("requester"), id=request_id
		)
		if blood_request.requester != request.user:
			return Response(
				{"success": False, "data": None, "message": "Only the request owner can complete this request."},
				status=status.HTTP_403_FORBIDDEN,
			)
		if blood_request.status != BloodRequest.Status.OPEN:
			return Response(
				{"success": False, "data": None, "message": "This request is already closed."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		donor_id = request.data.get("donor_id")
		donor_profile = get_object_or_404(
			DonorProfile.objects.select_related("user"), user_id=donor_id
		)
		if (
			donor_profile.blood_group != blood_request.blood_group
			or donor_profile.area != blood_request.area
		):
			return Response(
				{"success": False, "data": None, "message": "The donor does not match this request."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		try:
			with transaction.atomic():
				DonationHistory.objects.create(
					donor=donor_profile.user,
					blood_request=blood_request,
				)
				blood_request.status = BloodRequest.Status.FULFILLED
				blood_request.updated_at = timezone.now()
				blood_request.save(update_fields=["status", "updated_at"])
				donor_profile.is_available = False
				donor_profile.save(update_fields=["is_available", "updated_at"])
		except IntegrityError:
			return Response(
				{"success": False, "data": None, "message": "Donation history already exists for this request."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		return Response({"success": True, "data": request_data(blood_request), "message": "Request fulfilled."})


class BloodRequestCloseView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request, request_id):
		blood_request = get_object_or_404(BloodRequest, id=request_id)
		if blood_request.requester != request.user:
			return Response(
				{"success": False, "data": None, "message": "Only the request owner can close this request."},
				status=status.HTTP_403_FORBIDDEN,
			)
		if blood_request.status != BloodRequest.Status.OPEN:
			return Response(
				{"success": False, "data": None, "message": "This request is already closed."},
				status=status.HTTP_400_BAD_REQUEST,
			)
		blood_request.status = BloodRequest.Status.CLOSED
		blood_request.save(update_fields=["status", "updated_at"])
		return Response({"success": True, "data": request_data(blood_request), "message": "Request closed."})


class DonationHistoryView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		history = DonationHistory.objects.filter(donor=request.user).select_related("blood_request")
		data = [
			{
				"id": str(item.id),
				"request_id": str(item.blood_request_id),
				"blood_group": item.blood_request.blood_group,
				"area": item.blood_request.area,
				"hospital": item.blood_request.hospital,
				"donated_at": item.donated_at,
			}
			for item in history
		]
		return Response({"success": True, "data": data, "message": "Donation history loaded."})
