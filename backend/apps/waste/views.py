from django.db.models import Q
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .models import (
    WasteCollector,
    WasteCollectorRating,
    WastePickupRequest,
)
from .serializers import (
    WasteCollectorRatingSerializer,
    WasteCollectorSerializer,
    WastePickupRequestSerializer,
)

User = get_user_model()


class AvailableVolunteerCollectorsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        area = request.query_params.get("area", "").strip()
        volunteers = User.objects.filter(role="Volunteer")
        if area:
            volunteers = volunteers.filter(location__icontains=area)
        data = [
            {
                "user_id": str(volunteer.user_id),
                "full_name": volunteer.full_name,
                "location": volunteer.location,
            }
            for volunteer in volunteers.order_by("full_name")
        ]
        return Response({"success": True, "data": data})


class WastePickupRequestListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = WastePickupRequestSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):
        user = self.request.user

        queryset = WastePickupRequest.objects.all()

        if user.role == "Citizen" and not (
            user.is_staff or user.is_superuser
        ):
            return queryset.filter(
                requester=user
            )

        area = self.request.query_params.get(
            "area"
        )

        status_param = self.request.query_params.get(
            "status"
        )

        if area:
            queryset = queryset.filter(
                area__icontains=area
            )

        if status_param:
            queryset = queryset.filter(
                status__iexact=status_param
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            requester=self.request.user
        )


class WastePickupRequestDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = WastePickupRequestSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]

    lookup_field = "id"

    def get_queryset(self):
        queryset = WastePickupRequest.objects.select_related(
            "requester", "collector"
        )
        user = self.request.user
        if user.role == "Citizen" and not (user.is_staff or user.is_superuser):
            return queryset.filter(requester=user)
        return queryset

    def update(
        self,
        request,
        *args,
        **kwargs
    ):
        instance = self.get_object()
        user = request.user

        if (
            instance.requester != user
            and user.role
            not in ["Volunteer", "NGO", "Admin"]
            and not user.is_staff
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You do not have permission "
                        "to modify this request."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().update(
            request,
            *args,
            **kwargs
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.requester_id != request.user.pk and not (
            request.user.is_staff or request.user.is_superuser
        ):
            return Response(
                {
                    "success": False,
                    "message": "Only the requester or an administrator can delete this request.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class WasteCollectorListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = WasteCollectorSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):
        area = self.request.query_params.get(
            "area",
            "",
        ).strip()

        queryset = WasteCollector.objects.all()

        if area:
            queryset = queryset.filter(
                Q(area__icontains=area)
                | Q(name__icontains=area)
            )

        return queryset

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            "request": self.request,
        }

    def perform_create(self, serializer):
        serializer.save(
            shared_by=self.request.user
        )


class CollectorProfileView(APIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request, collector_id):
        try:
            collector = (
                WasteCollector.objects.get(
                    id=collector_id
                )
            )

        except WasteCollector.DoesNotExist:
            # Volunteer suggestions use User UUIDs, while shared collector
            # records use WasteCollector UUIDs. Support both existing IDs on
            # the collector details page without exposing private contact data.
            try:
                volunteer = User.objects.get(
                    user_id=collector_id,
                    role=User.Role.VOLUNTEER,
                )
            except (User.DoesNotExist, ValueError):
                return Response(
                    {"success": False, "message": "Collector not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            from apps.ratings.models import Rating

            ratings = Rating.objects.filter(rated_user=volunteer)
            return Response({
                "success": True,
                "profile_type": "volunteer_user",
                "data": {
                    "user_id": str(volunteer.user_id),
                    "full_name": volunteer.full_name,
                    "location": volunteer.location if volunteer.is_location_visible else "",
                    "phone_number": volunteer.phone_number if volunteer.is_phone_visible else "",
                    "average_rating": Rating.average_for_user(volunteer) or 0,
                    "rating_count": ratings.count(),
                },
            })

        serializer = WasteCollectorSerializer(
            collector,
            context={"request": request},
        )

        return Response(
            {
                "success": True,
                "profile_type": "shared_collector",
                "data": serializer.data,
            }
        )



class WasteCollectorRatingListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = WasteCollectorRatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        collector_id = self.kwargs["collector_id"]
        return WasteCollectorRating.objects.filter(
            collector_id=collector_id
        )

    def get_collector(self):
        collector_id = self.kwargs["collector_id"]

        try:
            return WasteCollector.objects.get(id=collector_id)
        except WasteCollector.DoesNotExist:
            raise serializers.ValidationError(
                "Waste collector not found."
            )

    def perform_create(self, serializer):
        collector = self.get_collector()
        if WasteCollectorRating.objects.filter(collector=collector, user=self.request.user).exists():
            raise serializers.ValidationError("You have already rated this collector.")
        serializer.save(collector=collector, user=self.request.user)
