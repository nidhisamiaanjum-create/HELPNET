from django.db.models import Count, IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsAdminUserRole
from .models import HealthProfessional, HealthQuestion, HealthReply
from .serializers import HealthProfessionalSerializer, HealthQuestionSerializer, HealthReplySerializer


class HealthQuestionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def question_queryset():
        reply_counts = (
            HealthReply.objects.filter(question_id=OuterRef("pk"))
            .order_by()
            .values("question_id")
            .annotate(total=Count("pk"))
            .values("total")[:1]
        )
        return (
            HealthQuestion.objects.select_related("author")
            .annotate(
                reply_count=Coalesce(Subquery(reply_counts), Value(0), output_field=IntegerField()),
            )
        )

    def get(self, request):
        questions = []
        seen_questions = set()
        for question in self.question_queryset():
            signature = (question.author_id, question.title, question.description, question.category)
            if signature not in seen_questions:
                seen_questions.add(signature)
                questions.append(question)
        return Response({"success": True, "data": HealthQuestionSerializer(questions, many=True).data, "message": "Health questions loaded."})

    def post(self, request):
        serializer = HealthQuestionSerializer(data=request.data)
        if serializer.is_valid():
            duplicate = HealthQuestion.objects.filter(
                author=request.user,
                title=serializer.validated_data["title"],
                description=serializer.validated_data["description"],
                category=serializer.validated_data["category"],
            ).first()
            if duplicate:
                duplicate.reply_count = duplicate.replies.count()
                return Response({"success": True, "data": HealthQuestionSerializer(duplicate).data, "message": "This question has already been submitted."})
            question = serializer.save(author=request.user)
            question.reply_count = 0
            return Response({"success": True, "data": HealthQuestionSerializer(question).data, "message": "Question created."}, status=status.HTTP_201_CREATED)
        return Response({"success": False, "data": None, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class HealthQuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, question_id):
        question = get_object_or_404(HealthQuestionListCreateView.question_queryset(), pk=question_id)
        return Response({"success": True, "data": HealthQuestionSerializer(question).data, "message": "Question loaded."})


class HealthReplyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, question_id):
        get_object_or_404(HealthQuestion, pk=question_id)
        replies = HealthReply.objects.filter(question_id=question_id).select_related("author")
        return Response({"success": True, "data": HealthReplySerializer(replies, many=True).data, "message": "Replies loaded."})

    def post(self, request, question_id):
        question = get_object_or_404(HealthQuestion, pk=question_id)
        serializer = HealthReplySerializer(data=request.data)
        if serializer.is_valid():
            reply = serializer.save(author=request.user, question=question)
            return Response({"success": True, "data": HealthReplySerializer(reply).data, "message": "Reply added."}, status=status.HTTP_201_CREATED)
        return Response({"success": False, "data": None, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class HealthProfessionalListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        professionals = HealthProfessional.objects.select_related("user")
        return Response({"success": True, "data": HealthProfessionalSerializer(professionals, many=True).data, "message": "Health professionals loaded."})


class HealthProfessionalVerificationView(APIView):
    permission_classes = [IsAdminUserRole]

    def patch(self, request, professional_id):
        professional = get_object_or_404(HealthProfessional, pk=professional_id)
        verification_status = request.data.get("verification_status")
        if verification_status not in HealthProfessional.VerificationStatus.values:
            return Response({"success": False, "data": None, "message": "Select a valid verification status."}, status=status.HTTP_400_BAD_REQUEST)
        professional.verification_status = verification_status
        professional.save(update_fields=["verification_status"])
        return Response({"success": True, "data": HealthProfessionalSerializer(professional).data, "message": "Professional verification status updated."})
