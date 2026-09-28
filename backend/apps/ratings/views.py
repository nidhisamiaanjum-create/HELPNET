from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Rating
from .serializers import RatingSerializer

User = get_user_model()


class RatingListCreateView(generics.ListCreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id") or self.request.query_params.get("rated_user")
        if user_id:
            return Rating.objects.filter(rated_user_id=user_id)
        return Rating.objects.filter(rater=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


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

        # Check if requesting user already rated target user
        user_rating = ratings.filter(rater=request.user).first()

        reviews_data = RatingSerializer(ratings[:10], many=True).data

        return Response({
            "success": True,
            "data": {
                "user_id": str(target_user.user_id),
                "full_name": target_user.full_name,
                "role": target_user.role,
                "location": target_user.location,
                "average_rating": round(avg_score, 1) if avg_score is not None else 5.0,
                "total_ratings": count,
                "user_has_rated": user_rating is not None,
                "user_rating_score": user_rating.score if user_rating else None,
                "user_rating_comment": user_rating.comment if user_rating else "",
                "recent_reviews": reviews_data,
            }
        })
