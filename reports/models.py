from django.db import models
from django.conf import settings


class Review(models.Model):
    book_title = models.CharField(max_length=255)   # temporary - paxi catalog.Book sanga link garne
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.book_title} ({self.rating}/5)"