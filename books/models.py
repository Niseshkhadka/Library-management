from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    available_copies = models.PositiveIntegerField(default=0)
    hold_copies = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def hold_copy(self):
        if self.available_copies > 0:
            self.available_copies -= 1
            self.hold_copies += 1
            self.save(update_fields=['available_copies', 'hold_copies'])

    def release_copy(self):
        if self.hold_copies > 0:
            self.available_copies += 1
            self.hold_copies -= 1
            self.save(update_fields=['available_copies', 'hold_copies'])

    def __str__(self):
        return self.title
