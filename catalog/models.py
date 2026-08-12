from django.db import models

# Create your models here.
class Book(models.Model):
    """DEMO placeholder — Person B will replace this with the full Catalog app
    (ISBN, genre, author FK, search/filter, etc.). Keep field names matching
    when merging so circulation's ForeignKey doesn't break."""

    title = models.CharField(max_length=255)
    available_copies = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title