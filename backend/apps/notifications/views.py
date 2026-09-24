from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification


def notification_data(notification):
	return {
		"id": str(notification.id),
		"message": notification.message,
		"notification_type": notification.notification_type,
		"is_read": notification.is_read,
		"created_at": notification.created_at,
	}


class NotificationListView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		notifications = Notification.objects.filter(user=request.user)
		return Response(
			{
				"success": True,
				"data": [notification_data(item) for item in notifications],
				"message": "Notifications loaded.",
			}
		)


class NotificationReadView(APIView):
	permission_classes = [IsAuthenticated]

	def mark_read(self, request, notification_id):
		notification = get_object_or_404(
			Notification,
			id=notification_id,
			user=request.user,
		)
		notification.is_read = True
		notification.save(update_fields=["is_read"])
		return Response(
			{
				"success": True,
				"data": notification_data(notification),
				"message": "Notification marked as read.",
			},
			status=status.HTTP_200_OK,
		)

	def post(self, request, notification_id):
		return self.mark_read(request, notification_id)

	def patch(self, request, notification_id):
		return self.mark_read(request, notification_id)
