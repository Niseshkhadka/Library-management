from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from catalog.models import Book
from .models import Loan, Fine
from .serializers import (
    LoanSerializer, BorrowRequestSerializer, ReturnRequestSerializer
)


class BorrowBookView(APIView):
    """POST /circulation/borrow/  { "book_id": 3 }"""

    def post(self, request):
        serializer = BorrowRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book_id = serializer.validated_data['book_id']

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        if book.available_copies < 1:
            return Response({"error": "No copies available"}, status=status.HTTP_400_BAD_REQUEST)

        loan = Loan.objects.create(user=request.user, book=book)
        book.available_copies -= 1
        book.save()

        return Response(LoanSerializer(loan).data, status=status.HTTP_201_CREATED)


class ReturnBookView(APIView):
    """POST /circulation/return/  { "loan_id": 7 }"""

    def post(self, request):
        serializer = ReturnRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan_id = serializer.validated_data['loan_id']

        try:
            loan = Loan.objects.get(id=loan_id, user=request.user, status__in=['borrowed', 'overdue'])
        except Loan.DoesNotExist:
            return Response({"error": "Active loan not found"}, status=status.HTTP_404_NOT_FOUND)

        loan.return_date = timezone.now()
        loan.status = 'returned'
        loan.save()

        # give the book copy back
        loan.book.available_copies += 1
        loan.book.save()

        # fine calculation: only if returned after due_date
        if loan.return_date > loan.due_date:
            days_late = (loan.return_date - loan.due_date).days
            amount = days_late * Fine.RATE_PER_DAY
            Fine.objects.create(loan=loan, amount=amount)

        return Response(LoanSerializer(loan).data, status=status.HTTP_200_OK)


class RenewLoanView(APIView):
    """POST /circulation/renew/  { "loan_id": 7 }"""

    def post(self, request):
        loan_id = request.data.get('loan_id')
        try:
            loan = Loan.objects.get(id=loan_id, user=request.user, status='borrowed')
        except Loan.DoesNotExist:
            return Response({"error": "Active loan not found"}, status=status.HTTP_404_NOT_FOUND)

        if loan.renewed_count >= Loan.MAX_RENEWALS:
            return Response({"error": "Renewal limit reached"}, status=status.HTTP_400_BAD_REQUEST)

        loan.due_date = loan.due_date + timedelta(days=Loan.DEFAULT_LOAN_DAYS)
        loan.renewed_count += 1
        loan.save()

        return Response(LoanSerializer(loan).data, status=status.HTTP_200_OK)


class LoanHistoryView(APIView):
    """GET /circulation/history/  — borrowing history for the logged-in user"""

    def get(self, request):
        loans = Loan.objects.filter(user=request.user).order_by('-borrow_date')
        return Response(LoanSerializer(loans, many=True).data)