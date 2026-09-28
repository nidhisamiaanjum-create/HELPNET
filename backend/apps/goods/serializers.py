from rest_framework import serializers
from .models import GoodsInterest, GoodsListing, GoodsReport


class GoodsListingSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.full_name", read_only=True)
    seller_contact = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = GoodsListing
        fields = [
            "id", "seller", "seller_name", "seller_contact", "title", "description",
            "condition", "asking_price", "location", "image", "image_url", "status",
            "created_at", "is_owner",
        ]
        read_only_fields = ["id", "seller", "seller_name", "seller_contact", "status", "created_at", "is_owner", "image_url"]

    def get_seller_contact(self, listing):
        request = self.context.get("request")
        seller = listing.seller
        is_self = request and request.user.is_authenticated and request.user.pk == seller.pk
        contact = {"full_name": seller.full_name}
        if is_self or seller.is_location_visible:
            contact["location"] = seller.location
        if is_self or seller.is_phone_visible:
            contact["phone_number"] = seller.phone_number
        if is_self or seller.is_email_visible:
            contact["email"] = seller.email
        return contact

    def get_image_url(self, listing):
        if not listing.image:
            return None
        url = listing.image.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def get_is_owner(self, listing):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and request.user.pk == listing.seller_id)


class GoodsInterestSerializer(serializers.ModelSerializer):
    interested_user_name = serializers.CharField(source="interested_user.full_name", read_only=True)

    class Meta:
        model = GoodsInterest
        fields = ["id", "listing", "interested_user", "interested_user_name", "created_at"]
        read_only_fields = ["id", "listing", "interested_user", "interested_user_name", "created_at"]


class GoodsReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source="reporter.full_name", read_only=True)

    class Meta:
        model = GoodsReport
        fields = ["id", "listing", "reporter", "reporter_name", "reason", "description", "status", "created_at"]
        read_only_fields = ["id", "listing", "reporter", "reporter_name", "status", "created_at"]
