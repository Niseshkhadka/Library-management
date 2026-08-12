from rest_framework import serializers
from .models import Author, Category, Book


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class BookSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'isbn', 'author', 'author_name',
            'category', 'category_name', 'description',
            'published_date', 'total_copies', 'available_copies',
            'cover_image', 'created_at', 'updated_at',
        ]