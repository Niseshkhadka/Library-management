from django.db import models
from django.contrib.auth.models import User


# Temporary Book model for development
# Remove this later when the books app is added
class Book(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class BorrowRecord(models.Model):
    # WHO borrowed the book
    member = models.ForeignKey(User, on_delete=models.CASCADE)

    # WHICH book was borrowed
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    # Automatically saves today's date when borrowed
    borrow_date = models.DateField(auto_now_add=True)

    # Due date for returning the book
    due_date = models.DateField()

    # Return date (empty until returned)
    return_date = models.DateField(null=True, blank=True)

    # Whether the book has been returned
    is_returned = models.BooleanField(default=False)

    # Number of renewals
    renewal_count = models.IntegerField(default=0)

    # Fine amount
    fine_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.member.username} - {self.book.title}"