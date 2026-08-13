from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Avg
from django.utils import timezone
from .models import Review
from .serializers import ReviewSerializer

# Group merge भएपछि यो uncomment गर्नु:
# from circulation.models import BorrowRecord


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total_reviews = Review.objects.count()
        top_rated_books = (
            Review.objects.values('book_title')
            .annotate(avg_rating=Avg('rating'), review_count=Count('id'))
            .order_by('-avg_rating')[:10]
        )
        active_reviewers = Review.objects.values('user').distinct().count()

        # ------------------------------------------------------------
        # GROUP MERGE भएपछि यो section activate गर्नु
        # (circulation app ko BorrowRecord model आएपछि):
        # ------------------------------------------------------------
        # most_borrowed = (
        #     BorrowRecord.objects.values('book__title')
        #     .annotate(count=Count('id'))
        #     .order_by('-count')[:10]
        # )
        # overdue_list = BorrowRecord.objects.filter(
        #     is_returned=False, due_date__lt=timezone.now()
        # ).values('user__username', 'book__title', 'due_date')
        # active_members = BorrowRecord.objects.values('user').distinct().count()
        # ------------------------------------------------------------

        return Response({
            "total_reviews": total_reviews,
            "top_rated_books": list(top_rated_books),
            "active_reviewers": active_reviewers,
            "note": "most_borrowed ra overdue_list circulation app merge bhaisakepachi activate huncha",
        })