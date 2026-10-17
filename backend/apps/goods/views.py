from django.db import IntegrityError, transaction
from django.db.models import OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports.models import Report
from apps.reports.serializers import ReportSerializer
from apps.notifications.models import Notification
from .models import GoodsConversation, GoodsInterest, GoodsListing, GoodsMessage, GoodsReport
from .serializers import GoodsInterestSerializer, GoodsListingSerializer, GoodsReportSerializer


VALID_GOODS_STATUS_TRANSITIONS = {
    GoodsListing.Status.AVAILABLE: {GoodsListing.Status.RESERVED, GoodsListing.Status.REMOVED},
    GoodsListing.Status.RESERVED: {GoodsListing.Status.AVAILABLE, GoodsListing.Status.EXCHANGED, GoodsListing.Status.REMOVED},
    GoodsListing.Status.EXCHANGED: {GoodsListing.Status.REMOVED},
    GoodsListing.Status.REMOVED: set(),
}


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
        if listing.status != GoodsListing.Status.AVAILABLE and listing.seller_id != request.user.pk:
            return Response({"success": False, "data": None, "message": "This listing is no longer available."}, status=404)
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
        allowed_next = VALID_GOODS_STATUS_TRANSITIONS.get(listing.status, set())
        if new_status not in allowed_next:
            return Response({"success": False, "data": None, "message": f"Status cannot change from {listing.status} to {new_status}."}, status=400)
        listing.status = new_status
        listing.save(update_fields=["status"])
        serializer = GoodsListingSerializer(listing, context={"request": request})
        return Response({"success": True, "data": serializer.data, "message": "Listing status updated."})


class GoodsInterestCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, listing_id):
        listing = get_object_or_404(GoodsListing, pk=listing_id)
        if listing.seller_id == request.user.pk:
            return Response({"success": False, "data": None, "message": "You cannot express interest in your own listing."}, status=400)
        if listing.status != GoodsListing.Status.AVAILABLE:
            return Response({"success": False, "data": None, "message": "This listing is not available for interest."}, status=400)
        created = False
        try:
            with transaction.atomic():
                interest, created = GoodsInterest.objects.get_or_create(listing=listing, interested_user=request.user)
                conversation, _ = GoodsConversation.objects.get_or_create(
                    listing=listing, owner=listing.seller, interested_user=request.user
                )
                if created:
                    Notification.objects.create(
                        user=listing.seller,
                        message=f"{request.user.full_name} is interested in your listing '{listing.title}'.",
                        notification_type="goods_interest",
                        action_url=f"/goods-chat/?conversation_id={conversation.pk}",
                    )
        except IntegrityError:
            interest = GoodsInterest.objects.get(listing=listing, interested_user=request.user)
            conversation = GoodsConversation.objects.get(listing=listing, owner=listing.seller, interested_user=request.user)
        serializer = GoodsInterestSerializer(interest)
        return Response({"success": True, "data": {**serializer.data, "conversation_id": conversation.pk, "conversation_url": f"/goods-chat/?conversation_id={conversation.pk}"}, "message": "Interest sent to the listing owner." if created else "You have already expressed interest. Open your existing conversation."}, status=201 if created else 200)


def conversation_or_404(conversation_id):
    return get_object_or_404(
        GoodsConversation.objects.select_related("listing", "owner", "interested_user"),
        pk=conversation_id,
    )


class GoodsConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        latest_messages = GoodsMessage.objects.filter(conversation_id=OuterRef("pk")).order_by("-created_at", "-pk")
        items = GoodsConversation.objects.filter(
            Q(owner=request.user) | Q(interested_user=request.user)
        ).select_related("listing", "owner", "interested_user").annotate(
            latest_message_text=Subquery(latest_messages.values("message")[:1]),
            latest_message_at=Subquery(latest_messages.values("created_at")[:1]),
        )
        data = []
        for item in items:
            other = item.interested_user if item.owner_id == request.user.pk else item.owner
            data.append({"id": item.pk, "listing_id": item.listing_id, "listing_title": item.listing.title,
                         "other_user_name": other.full_name, "latest_message": item.latest_message_text or "",
                         "latest_message_at": item.latest_message_at or item.created_at,
                         "url": f"/goods-chat/?conversation_id={item.pk}"})
        return Response({"success": True, "data": data, "message": "Conversations loaded."})


class GoodsConversationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        conversation = conversation_or_404(conversation_id)
        if request.user.pk not in (conversation.owner_id, conversation.interested_user_id):
            return Response({"success": False, "data": None, "message": "You cannot access this conversation."}, status=403)
        messages = conversation.messages.select_related("sender").all()
        data = [{"id": m.pk, "sender_id": m.sender_id, "sender_name": m.sender.full_name,
                 "message": m.message, "created_at": m.created_at} for m in messages]
        return Response({"success": True, "data": {"id": conversation.pk, "listing_id": conversation.listing_id,
            "listing_title": conversation.listing.title, "owner_id": conversation.owner_id,
            "other_user_name": conversation.interested_user.full_name if request.user.pk == conversation.owner_id else conversation.owner.full_name,
            "messages": data}, "message": "Conversation loaded."})

    def post(self, request, conversation_id):
        conversation = conversation_or_404(conversation_id)
        if request.user.pk not in (conversation.owner_id, conversation.interested_user_id):
            return Response({"success": False, "data": None, "message": "You cannot access this conversation."}, status=403)
        message = request.data.get("message")
        if not isinstance(message, str) or not message.strip():
            return Response({"success": False, "data": None, "message": "Message cannot be empty."}, status=400)
        if len(message.strip()) > 2000:
            return Response({"success": False, "data": None, "message": "Message must be 2000 characters or fewer."}, status=400)
        item = GoodsMessage.objects.create(conversation=conversation, sender=request.user, message=message.strip())
        conversation.save(update_fields=["updated_at"])
        return Response({"success": True, "data": {"id": item.pk, "sender_id": item.sender_id, "sender_name": item.sender.full_name,
            "message": item.message, "created_at": item.created_at}, "message": "Message sent."}, status=201)


class GoodsInterestedUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, listing_id):
        listing = get_object_or_404(GoodsListing, pk=listing_id)
        if listing.seller_id != request.user.pk:
            return Response({"success": False, "data": None, "message": "Only the listing owner can view interested users."}, status=403)
        interests = listing.interests.select_related("interested_user").all()
        data = []
        for interest in interests:
            conversation, _ = GoodsConversation.objects.get_or_create(listing=listing, owner=listing.seller, interested_user=interest.interested_user)
            data.append({"user_id": interest.interested_user_id, "user_name": interest.interested_user.full_name,
                         "created_at": interest.created_at, "conversation_id": conversation.pk,
                         "conversation_url": f"/goods-chat/?conversation_id={conversation.pk}"})
        return Response({"success": True, "data": data, "message": "Interested users loaded."})


class GoodsReportCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, listing_id):
        listing = get_object_or_404(GoodsListing, pk=listing_id)
        reason = str(request.data.get("reason", "")).strip()
        description = str(request.data.get("description", "")).strip()
        if not reason:
            return Response({"success": False, "data": None, "message": "A report reason is required."}, status=400)
        report = Report.objects.create(
            reporter=request.user,
            reported_user=listing.seller,
            content_object=listing,
            category=Report.Category.FRAUD,
            description=f"{reason}\n{description}".strip(),
        )
        return Response({"success": True, "data": ReportSerializer(report).data, "message": "Listing reported."}, status=201)
