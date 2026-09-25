from datetime import date
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from reportlab.pdfgen import canvas
from io import BytesIO
from .models import VolunteerOpportunity, VolunteerProfile, VolunteerSignup, VolunteerAttendance, VolunteerMessage, VolunteerCertificate
from .serializers import VolunteerOpportunitySerializer, VolunteerProfileSerializer, VolunteerSignupSerializer, VolunteerAttendanceSerializer, VolunteerMessageSerializer, VolunteerCertificateSerializer


def coordinator(user):
    return user.is_authenticated and (user.role == "NGO" or user.is_staff or user.is_superuser)


def event_or_404(event_id):
    return get_object_or_404(VolunteerOpportunity.objects.select_related("coordinator"), pk=event_id)


class OpportunityListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = VolunteerOpportunity.objects.select_related("coordinator")
        if request.query_params.get("all") != "true":
            events = events.filter(status=VolunteerOpportunity.Status.OPEN)
        return Response({"success": True, "data": VolunteerOpportunitySerializer(events, many=True).data})

    def post(self, request):
        if not coordinator(request.user):
            return Response({"success": False, "message": "Only NGO coordinators can create opportunities."}, status=403)
        serializer = VolunteerOpportunitySerializer(data=request.data)
        if serializer.is_valid():
            event = serializer.save(coordinator=request.user)
            return Response({"success": True, "data": VolunteerOpportunitySerializer(event).data}, status=201)
        return Response({"success": False, "message": serializer.errors}, status=400)


class OpportunityDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, event_id):
        return Response({"success": True, "data": VolunteerOpportunitySerializer(event_or_404(event_id)).data})
    def patch(self, request, event_id):
        event = event_or_404(event_id)
        if not coordinator(request.user) or event.coordinator_id != request.user.user_id:
            return Response({"success": False, "message": "Only this event's coordinator can update it."}, status=403)
        new_status = request.data.get("status")
        if new_status not in VolunteerOpportunity.Status.values:
            return Response({"success": False, "message": "Status must be Open or Closed."}, status=400)
        event.status = new_status
        event.save(update_fields=["status"])
        return Response({"success": True, "data": VolunteerOpportunitySerializer(event).data})


class MyVolunteerEventsView(APIView):
    """Return events the signed-in user coordinates or has joined."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        coordinated_only = request.query_params.get("coordinated") == "true"
        if coordinated_only:
            if not coordinator(request.user):
                return Response({"success": False, "message": "Coordinator access required."}, status=403)
            events = VolunteerOpportunity.objects.filter(coordinator=request.user)
        else:
            events = VolunteerOpportunity.objects.filter(
                Q(coordinator=request.user) | Q(signups__volunteer=request.user)
            )
        events = events.select_related("coordinator").distinct()
        return Response({"success": True, "data": VolunteerOpportunitySerializer(events, many=True).data})


class VolunteerSignupView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, event_id):
        event = event_or_404(event_id)
        if not coordinator(request.user) or event.coordinator_id != request.user.user_id:
            return Response({"success": False, "message": "Only this event's coordinator can view signups."}, status=403)
        qs = VolunteerSignup.objects.filter(event=event).select_related("volunteer")
        return Response({"success": True, "data": VolunteerSignupSerializer(qs, many=True).data})

    def post(self, request, event_id):
        if request.user.role != "Volunteer":
            return Response({"success": False, "message": "Only volunteer accounts can sign up."}, status=403)
        event = event_or_404(event_id)
        if event.status != VolunteerOpportunity.Status.OPEN:
            return Response({"success": False, "message": "This opportunity is closed."}, status=400)
        try:
            # Isolate the unique-constraint violation so a duplicate signup does
            # not leave an enclosing request/test transaction unusable.
            with transaction.atomic():
                signup = VolunteerSignup.objects.create(volunteer=request.user, event=event)
        except IntegrityError:
            return Response({"success": False, "message": "You have already signed up."}, status=400)
        return Response({"success": True, "data": VolunteerSignupSerializer(signup).data}, status=201)


class VolunteerProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        profile, _ = VolunteerProfile.objects.get_or_create(user=request.user)
        return Response({"success": True, "data": VolunteerProfileSerializer(profile).data})
    def put(self, request):
        if request.user.role != "Volunteer":
            return Response({"success": False, "message": "Only volunteer accounts can update this profile."}, status=403)
        profile, _ = VolunteerProfile.objects.get_or_create(user=request.user)
        serializer = VolunteerProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "data": serializer.data})
        return Response({"success": False, "message": serializer.errors}, status=400)


class AttendanceView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, event_id):
        event = event_or_404(event_id)
        if not coordinator(request.user) or event.coordinator_id != request.user.user_id:
            return Response({"success": False, "message": "Only this event's coordinator can manage attendance."}, status=403)
        for signup in VolunteerSignup.objects.filter(event=event).only("volunteer_id"):
            VolunteerAttendance.objects.get_or_create(event=event, volunteer_id=signup.volunteer_id)
        qs = VolunteerAttendance.objects.filter(event=event).select_related("volunteer")
        return Response({"success": True, "data": VolunteerAttendanceSerializer(qs, many=True).data})
    def post(self, request, event_id):
        event = event_or_404(event_id)
        if not coordinator(request.user) or event.coordinator_id != request.user.user_id:
            return Response({"success": False, "message": "Only this event's coordinator can manage attendance."}, status=403)
        volunteer = get_object_or_404(VolunteerSignup, event=event, volunteer_id=request.data.get("volunteer_id")).volunteer
        attendance, _ = VolunteerAttendance.objects.get_or_create(event=event, volunteer=volunteer)
        action = request.data.get("action")
        if action == "check_in":
            attendance.check_in_time = timezone.now()
        elif action == "check_out":
            if not attendance.check_in_time:
                return Response({"success": False, "message": "Check in this volunteer first."}, status=400)
            attendance.check_out_time = timezone.now()
        else:
            return Response({"success": False, "message": "Action must be check_in or check_out."}, status=400)
        attendance.save()
        return Response({"success": True, "data": VolunteerAttendanceSerializer(attendance).data})


class EventMessagesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, event_id):
        event = event_or_404(event_id)
        is_owner = coordinator(request.user) and event.coordinator_id == request.user.user_id
        is_participant = VolunteerSignup.objects.filter(event=event, volunteer=request.user).exists()
        if not (is_owner or is_participant):
            return Response({"success": False, "message": "Sign up for this event to view its messages."}, status=403)
        items = VolunteerMessage.objects.filter(event=event).select_related("sender")
        return Response({"success": True, "data": VolunteerMessageSerializer(items, many=True).data})
    def post(self, request, event_id):
        event = event_or_404(event_id)
        allowed = (coordinator(request.user) and event.coordinator_id == request.user.user_id) or VolunteerSignup.objects.filter(event=event, volunteer=request.user).exists()
        if not allowed:
            return Response({"success": False, "message": "Only event participants can send messages."}, status=403)
        serializer = VolunteerMessageSerializer(data={"event": event.pk, "message": request.data.get("message", "")})
        if serializer.is_valid():
            msg = serializer.save(sender=request.user)
            return Response({"success": True, "data": VolunteerMessageSerializer(msg).data}, status=201)
        return Response({"success": False, "message": serializer.errors}, status=400)


class CertificateListIssueView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, event_id=None):
        qs = VolunteerCertificate.objects.select_related("event", "volunteer", "coordinator")
        if request.user.role == "Volunteer":
            qs = qs.filter(volunteer=request.user)
        elif event_id:
            event = event_or_404(event_id)
            if not coordinator(request.user) or event.coordinator_id != request.user.user_id:
                return Response({"success": False, "message": "Only this event's coordinator can view certificates."}, status=403)
            qs = qs.filter(event=event)
        else:
            qs = qs.filter(coordinator=request.user)
        return Response({"success": True, "data": VolunteerCertificateSerializer(qs, many=True).data})
    def post(self, request, event_id):
        event = event_or_404(event_id)
        if not coordinator(request.user) or event.coordinator_id != request.user.user_id:
            return Response({"success": False, "message": "Only this event's coordinator can issue certificates."}, status=403)
        volunteer = get_object_or_404(VolunteerSignup, event=event, volunteer_id=request.data.get("volunteer_id")).volunteer
        if not VolunteerAttendance.objects.filter(event=event, volunteer=volunteer, check_in_time__isnull=False, check_out_time__isnull=False).exists():
            return Response({"success": False, "message": "A certificate requires completed attendance."}, status=400)
        certificate, created = VolunteerCertificate.objects.get_or_create(volunteer=volunteer, event=event, defaults={"coordinator": request.user, "completion_date": date.today()})
        return Response({"success": True, "data": VolunteerCertificateSerializer(certificate).data}, status=201 if created else 200)


class CertificatePdfView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, certificate_id):
        certificate = get_object_or_404(VolunteerCertificate.objects.select_related("volunteer", "event", "coordinator"), pk=certificate_id)
        if request.user != certificate.volunteer and request.user != certificate.coordinator and not request.user.is_staff:
            return Response({"success": False, "message": "You cannot access this certificate."}, status=403)
        output = BytesIO()
        pdf = canvas.Canvas(output)
        pdf.setTitle("Volunteer completion certificate")
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawCentredString(300, 740, "Certificate of Completion")
        pdf.setFont("Helvetica", 13)
        pdf.drawCentredString(300, 680, "This certificate is presented to")
        pdf.setFont("Helvetica-Bold", 19)
        pdf.drawCentredString(300, 640, certificate.volunteer.full_name)
        pdf.setFont("Helvetica", 13)
        pdf.drawCentredString(300, 590, f"For completing volunteer service: {certificate.event.title}")
        pdf.drawCentredString(300, 560, f"Completion date: {certificate.completion_date}")
        pdf.drawCentredString(300, 510, f"Organization / Coordinator: {certificate.coordinator.full_name}")
        pdf.save()
        response = HttpResponse(output.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="volunteer-certificate-{certificate.pk}.pdf"'
        return response


class VolunteerSearchView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not coordinator(request.user):
            return Response({"success": False, "message": "Only NGO coordinators can search volunteers."}, status=403)
        profiles = VolunteerProfile.objects.select_related("user").filter(user__role="Volunteer")
        for field in ("skills", "availability", "location"):
            value = request.query_params.get(field, "").strip()
            if value:
                profiles = profiles.filter(**{f"{field}__icontains": value})
        return Response({"success": True, "data": [{**VolunteerProfileSerializer(p).data, "email": p.user.email, "phone_number": p.user.phone_number} for p in profiles]})


class AdminVolunteersView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not (request.user.role == "Admin" or request.user.is_staff or request.user.is_superuser):
            return Response({"success": False, "message": "Administrator access required."}, status=403)
        profiles = VolunteerProfile.objects.select_related("user").filter(user__role="Volunteer")
        for field in ("skills", "availability", "location", "blood_group"):
            value = request.query_params.get(field, "").strip()
            if value:
                profiles = profiles.filter(**{f"{field}__icontains": value})
        data = [{**VolunteerProfileSerializer(p).data, "email": p.user.email, "phone_number": p.user.phone_number} for p in profiles]
        return Response({"success": True, "data": data})
