from django.db.models import Avg, Max, Min, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.reports.models import Report
from .models import ProduceListing
from .serializers import ProduceListingSerializer


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.farmer == request.user or request.user.is_staff


class ProduceListingListCreateView(generics.ListCreateAPIView):
    serializer_class = ProduceListingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ProduceListing.objects.all()

        search = self.request.query_params.get("search", "").strip()
        location = self.request.query_params.get("location", "").strip()
        category = self.request.query_params.get("category", "").strip()
        availability = self.request.query_params.get("availability", "").strip()

        if search:
            queryset = queryset.filter(
                Q(produce_name__icontains=search)
                | Q(description__icontains=search)
                | Q(location__icontains=search)
                | Q(farmer__full_name__icontains=search)
            )
        if location:
            queryset = queryset.filter(location__icontains=location)
        if category:
            queryset = queryset.filter(category__iexact=category)
        if availability:
            queryset = queryset.filter(availability__iexact=availability)

        return queryset

    def perform_create(self, serializer):
        serializer.save(farmer=self.request.user)


class ProduceListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProduceListingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    queryset = ProduceListing.objects.all()
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.farmer != request.user and not request.user.is_staff:
            return Response(
                {"success": False, "message": "You can only edit your own produce listings."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.farmer != request.user and not request.user.is_staff:
            return Response(
                {"success": False, "message": "You can only delete your own produce listings."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class MyProduceListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        listings = ProduceListing.objects.filter(farmer=request.user)
        serializer = ProduceListingSerializer(listings, many=True, context={"request": request})
        return Response({
            "success": True,
            "data": serializer.data,
            "count": len(serializer.data),
        })


class ProducePriceRangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        listing = get_object_or_404(ProduceListing, id=id)
        prices = ProduceListing.objects.filter(
            category__iexact=listing.category,
            location__iexact=listing.location,
            availability=ProduceListing.Availability.AVAILABLE,
        ).exclude(farmer_id=listing.farmer_id)
        summary = prices.aggregate(minimum=Min("price"), maximum=Max("price"), average=Avg("price"))
        summary["count"] = prices.count()
        return Response({"success": True, "data": summary, "message": "Active farmer listing prices loaded."})


class ProduceListingReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        listing = get_object_or_404(ProduceListing, id=id)
        description = str(request.data.get("description", "")).strip()
        if not description:
            return Response({"success": False, "message": "A report description is required."}, status=status.HTTP_400_BAD_REQUEST)
        report = Report.objects.create(
            reporter=request.user,
            reported_user=listing.farmer,
            content_object=listing,
            category=Report.Category.FRAUD,
            description=description,
        )
        return Response({"success": True, "data": {"id": str(report.pk)}, "message": "Listing reported."}, status=status.HTTP_201_CREATED)
