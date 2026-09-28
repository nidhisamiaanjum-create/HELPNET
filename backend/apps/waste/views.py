from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WastePickupRequest
from .serializers import CollectorUserSerializer, WastePickupRequestSerializer

User = get_user_model()


class WastePickupRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = WastePickupRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = WastePickupRequest.objects.all()

        # If citizen, only view their own requests
        if user.role == "Citizen" and not (user.is_staff or user.is_superuser):
            return queryset.filter(requester=user)

        # For volunteers, collectors, admins - can view all or filter by area / status
        area = self.request.query_params.get("area")
        status_param = self.request.query_params.get("status")

        if area:
            queryset = queryset.filter(area__icontains=area)
        if status_param:
            queryset = queryset.filter(status__iexact=status_param)

        return queryset

    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)


class WastePickupRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WastePickupRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = WastePickupRequest.objects.all()
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        # Ensure citizen can update their own request, or volunteers/staff can update status
        if instance.requester != user and user.role not in ["Volunteer", "NGO", "Admin"] and not user.is_staff:
            return Response(
                {"success": False, "message": "You do not have permission to modify this request."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().update(request, *args, **kwargs)


class AvailableCollectorsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        area = request.query_params.get("area", "").strip()

        # Target collectors (Volunteers, NGOs, or all non-citizen service providers if specified)
        collectors_qs = User.objects.filter(
            Q(role__in=["Volunteer", "NGO"]) | Q(role="Admin")
        )

        if area:
            # Simple area matching by location field (case-insensitive substring match)
            matched = collectors_qs.filter(
                Q(location__icontains=area) | Q(full_name__icontains=area)
            )
            # If matches found, use them; if none found, return general area collectors
            if matched.exists():
                collectors = matched
            else:
                collectors = collectors_qs
        else:
            collectors = collectors_qs

        serializer = CollectorUserSerializer(collectors, many=True)
        return Response({
            "success": True,
            "data": serializer.data,
            "area_queried": area,
            "count": len(serializer.data),
        })


class CollectorProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        try:
            collector = User.objects.get(user_id=user_id)
        except (User.DoesNotExist, ValueError):
            return Response(
                {"success": False, "message": "Collector not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CollectorUserSerializer(collector)
        return Response({
            "success": True,
            "data": serializer.data,
        })
