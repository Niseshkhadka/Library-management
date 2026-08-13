from django.urls import path
from .views import BorrowBookView, ReturnBookView, RenewLoanView, LoanHistoryView

urlpatterns = [
    path('borrow/', BorrowBookView.as_view(), name='borrow-book'),
    path('return/', ReturnBookView.as_view(), name='return-book'),
    path('renew/', RenewLoanView.as_view(), name='renew-loan'),
    path('history/', LoanHistoryView.as_view(), name='loan-history'),
]