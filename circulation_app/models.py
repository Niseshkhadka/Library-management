from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta


class Loan(models.Model):
    """Represents one borrow/issue transaction of a book by a user."""

    STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loans',
    )
    book = models.ForeignKey(
        'catalog.Book',
        on_delete=models.CASCADE,
        related_name='loans',
    )
    borrow_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='borrowed')
    renewed_count = models.PositiveSmallIntegerField(default=0)

    DEFAULT_LOAN_DAYS = 14
    MAX_RENEWALS = 2

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = timezone.now() + timedelta(days=self.DEFAULT_LOAN_DAYS)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} — {self.book} ({self.status})"


class Fine(models.Model):
    """Fine generated for a late return, linked one-to-one with the loan."""

    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name='fine')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    RATE_PER_DAY = 10  # currency units per day late — adjust as your team decides

    def __str__(self):
        return f"Fine {self.amount} for {self.loan}"