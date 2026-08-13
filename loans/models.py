from django.conf import settings
from django.db import models


class Loan(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_RETURNED = 'returned'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_RETURNED, 'Returned'),
    ]

    book = models.ForeignKey('books.Book', on_delete=models.PROTECT, related_name='loans')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    due_date = models.DateTimeField()
    returned_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_returned(self):
        self.returned_date = timezone.now()
        self.status = self.STATUS_RETURNED
        self.save(update_fields=['returned_date', 'status'])

    def __str__(self):
        return f'Loan {self.id} for {self.book}'
