from django.contrib import admin
from .models import Loan, Fine


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'borrow_date', 'due_date', 'status', 'renewed_count')
    list_filter = ('status',)
    search_fields = ('user__username', 'book__title')


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ('id', 'loan', 'amount', 'is_paid', 'created_at')
    list_filter = ('is_paid',)