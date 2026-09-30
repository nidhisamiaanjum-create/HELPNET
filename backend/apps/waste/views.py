from django.db.models import Q
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

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

    queryset = WastePickupRequest.objects.all()

    lookup_field = "id"

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
            return Response(
                {
                    "success": False,
                    "message": "Collector not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = WasteCollectorSerializer(
            collector,
            context={"request": request},
        )

        return Response(
            {
                "success": True,
                "data": serializer.data,
            }
        )


class WasteCollectorRatingListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = (
        WasteCollectorRatingSerializer
    )

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):
        collector_id = self.kwargs[
            "collector_id"
        ]

        return WasteCollectorRating.objects.filter(
            collector_id=collector_id
        )

    def perform_create(self, serializer):
        collector_id = self.kwargs[
            "collector_id"
        ]

        try:
            collector = (
                WasteCollector.objects.get(
                    id=collector_id
                )
            )

        except WasteCollector.DoesNotExist:
            raise serializers.ValidationError(
                "Waste collector not found."
            )

        already_rated = (
            WasteCollectorRating.objects.filter(
                collector=collector,
                user=self.request.user,
            ).exists()
        )

        if already_rated:
            raise serializers.ValidationError(
                "You have already rated this collector."
            )

        serializer.save(
            collector=collector,
            user=self.request.user,
        )