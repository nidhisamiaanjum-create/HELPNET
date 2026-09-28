from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Rating
from .serializers import RatingSerializer

User = get_user_model()


def rating_data(rating):
    return {
        "id": str(rating.id),
        "rater": str(rating.rater.user_id),
        "rater_name": rating.rater.full_name,
        "rated_user": str(rating.rated_user.user_id),
        "rating": rating.rating,
        "score": rating.rating,
        "comment": rating.comment,
        "created_at": rating.created_at,
    }


class RatingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.query_params.get("user_id") or request.query_params.get("rated_user")
        if user_id:
            ratings = Rating.objects.filter(rated_user_id=user_id).select_related("rater", "rated_user")
        else:
            ratings = Rating.objects.filter(rater=request.user).select_related("rater", "rated_user")
        return Response({
            "success": True,
            "data": [rating_data(r) for r in ratings],
            "message": "Ratings loaded."
        })

    def post(self, request):
        rated_user_id = request.data.get("rated_user")
        rating_value = request.data.get("rating") if "rating" in request.data else request.data.get("score")
        comment = request.data.get("comment", "")

        if not rated_user_id or rating_value in (None, ""):
            return Response(
                {"success": False, "data": None, "message": "rated_user and rating are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parsed_rating = int(rating_value)
        except (TypeError, ValueError):
            parsed_rating = None

        if isinstance(rating_value, bool) or (
            isinstance(rating_value, float) and not rating_value.is_integer()
        ):
            parsed_rating = None

        rating_value = parsed_rating
        if rating_value not in range(1, 6):
            rating_value = None

        if rating_value is None:
            return Response(
                {"success": False, "data": None, "message": "Rating must be between 1 and 5."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rated_user = User.objects.get(user_id=rated_user_id)
        except (User.DoesNotExist, ValueError):
            return Response(
                {"success": False, "data": None, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if rated_user == request.user:
            return Response(
                {"success": False, "data": None, "message": "You cannot rate yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rating = Rating.objects.create(
                rater=request.user,
                rated_user=rated_user,
                rating=rating_value,
                comment=str(comment).strip(),
            )
        except IntegrityError:
            return Response(
                {"success": False, "data": None, "message": "You have already rated this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"success": True, "data": rating_data(rating), "message": "Rating submitted successfully."},
            status=status.HTTP_201_CREATED,
        )


RatingListCreateView = RatingCreateView


class UserRatingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        rated_user = get_object_or_404(User, user_id=user_id)
        ratings = Rating.objects.filter(rated_user=rated_user).select_related("rater")
        return Response(
            {
                "success": True,
                "data": [rating_data(rating) for rating in ratings],
                "message": "Ratings loaded.",
            }
        )


class UserRatingAverageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        rated_user = get_object_or_404(User, user_id=user_id)
        ratings = Rating.objects.filter(rated_user=rated_user)
        return Response(
            {
                "success": True,
                "data": {
                    "user_id": str(rated_user.user_id),
                    "average_rating": Rating.average_for_user(rated_user),
                    "rating_count": ratings.count(),
                },
                "message": "Average rating loaded.",
            }
        )


class UserRatingSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        try:
            target_user = User.objects.get(user_id=user_id)
        except (User.DoesNotExist, ValueError):
            return Response(
                {"success": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        avg_score = Rating.average_for_user(target_user)
        ratings = Rating.objects.filter(rated_user=target_user)
        count = ratings.count()

        user_rating = ratings.filter(rater=request.user).first()
        reviews_data = RatingSerializer(ratings[:10], many=True).data

        return Response({
            "success": True,
            "data": {
                "user_id": str(target_user.user_id),
                "full_name": target_user.full_name,
                "role": target_user.role,
                "location": getattr(target_user, "location", ""),
                "average_rating": round(avg_score, 1) if avg_score is not None else 5.0,
                "total_ratings": count,
                "user_has_rated": user_rating is not None,
                "user_rating_score": user_rating.rating if user_rating else None,
                "user_rating_comment": user_rating.comment if user_rating else "",
                "recent_reviews": reviews_data,
            }
        })
