from rest_framework import serializers
from .models import Loan, Fine


class FineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fine
        fields = ['id', 'loan', 'amount', 'is_paid', 'created_at']
        read_only_fields = ['id', 'created_at']


class LoanSerializer(serializers.ModelSerializer):
    # Nested read-only fine info, shown automatically if a fine exists
    fine = FineSerializer(read_only=True)

    class Meta:
        model = Loan
        fields = [
            'id', 'user', 'book', 'borrow_date', 'due_date',
            'return_date', 'status', 'renewed_count', 'fine',
        ]
        read_only_fields = ['id', 'borrow_date', 'return_date', 'status', 'renewed_count']


class BorrowRequestSerializer(serializers.Serializer):
    """Not tied to a model — just validates the input when a user wants to borrow a book."""
    book_id = serializers.IntegerField()


class ReturnRequestSerializer(serializers.Serializer):
    """Validates the input when a user returns a book."""
    loan_id = serializers.IntegerField()