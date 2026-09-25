from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GoodsInterest, GoodsListing, GoodsReport
from .serializers import GoodsInterestSerializer, GoodsListingSerializer, GoodsReportSerializer


class GoodsListingListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get(self, request):
        listings = GoodsListing.objects.filter(status=GoodsListing.Status.AVAILABLE).select_related("seller")
        serializer = GoodsListingSerializer(listings, many=True, context={"request": request})
        return Response({"success": True, "data": serializer.data, "message": "Available goods loaded."})

    def post(self, request):
        serializer = GoodsListingSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            listing = serializer.save(seller=request.user)
            return Response(
                {"success": True, "data": GoodsListingSerializer(listing, context={"request": request}).data, "message": "Listing created."},
                status=201,
            )
        return Response({"success": False, "data": None, "message": serializer.errors}, status=400)


class GoodsListingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, listing_id):
        listing = get_object_or_404(GoodsListing.objects.select_related("seller"), pk=listing_id)
        serializer = GoodsListingSerializer(listing, context={"request": request})
        return Response({"success": True, "data": serializer.data, "message": "Listing loaded."})


class GoodsListingStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, listing_id):
        listing = get_object_or_404(GoodsListing, pk=listing_id)
        if listing.seller_id != request.user.pk:
            return Response({"success": False, "data": None, "message": "Only the listing owner can change its status."}, status=403)
        new_status = request.data.get("status")
        if new_status not in GoodsListing.Status.values:
            return Response({"success": False, "data": None, "message": "Select a valid listing status."}, status=400)
        listing.status = new_status
        listing.save(update_fields=["status"])
        serializer = GoodsListingSerializer(listing, context={"request": request})
        return Response({"success": True, "data": serializer.data, "message": "Listing status updated."})


class GoodsInterestCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, listing_id):
        listing = get_object_or_404(GoodsListing, pk=listing_id)
        if listing.status != GoodsListing.Status.AVAILABLE:
            return Response({"success": False, "data": None, "message": "This listing is not available for interest."}, status=400)
        try:
            with transaction.atomic():
                interest = GoodsInterest.objects.create(listing=listing, interested_user=request.user)
        except IntegrityError:
            return Response({"success": False, "data": None, "message": "You have already expressed interest in this listing."}, status=400)
        serializer = GoodsInterestSerializer(interest)
        return Response({"success": True, "data": serializer.data, "message": "Interest sent to the listing owner."}, status=201)


class GoodsReportCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, listing_id):
        listing = get_object_or_404(GoodsListing, pk=listing_id)
        serializer = GoodsReportSerializer(data=request.data)
        if serializer.is_valid():
            report = serializer.save(listing=listing, reporter=request.user)
            return Response({"success": True, "data": GoodsReportSerializer(report).data, "message": "Listing reported."}, status=201)
        return Response({"success": False, "data": None, "message": serializer.errors}, status=400)
