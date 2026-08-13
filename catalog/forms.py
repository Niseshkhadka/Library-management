from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'isbn', 'author', 'category', 'description',
                  'published_date', 'total_copies', 'available_copies', 'cover_image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'published_date': forms.DateInput(attrs={'type': 'date'}),
        }