from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from accounts.permissions import IsLibrarianOrSuperAdmin
from .models import Author, Category, Book
from .serializers import AuthorSerializer, CategorySerializer, BookSerializer
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .forms import BookForm


@login_required
def add_book_page(request):
    if request.user.role not in ['LIBRARIAN', 'SUPERADMIN']:
        return render(request, 'catalog/not_authorized.html')

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('book-list-page')
    else:
        form = BookForm()

    return render(request, 'catalog/add_book.html', {'form': form})


def book_detail_page(request, pk):
    book = get_object_or_404(Book.objects.select_related('author', 'category'), pk=pk)
    return render(request, 'catalog/book_detail.html', {'book': book})


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsLibrarianOrSuperAdmin()]
        return [IsAuthenticatedOrReadOnly()]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsLibrarianOrSuperAdmin()]
        return [IsAuthenticatedOrReadOnly()]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'author']
    search_fields = ['title', 'isbn']
    ordering_fields = ['title', 'published_date', 'total_copies']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsLibrarianOrSuperAdmin()]
        return [IsAuthenticatedOrReadOnly()]


def book_list_page(request):
    books = Book.objects.select_related('author', 'category').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        books = books.filter(title__icontains=search_query) | books.filter(isbn__icontains=search_query)
    
    # Category filter
    category_filter = request.GET.get('category', '')
    if category_filter:
        books = books.filter(category__id=category_filter)
    
    # Author filter
    author_filter = request.GET.get('author', '')
    if author_filter:
        books = books.filter(author__id=author_filter)
    
    # Availability filter
    availability_filter = request.GET.get('availability', '')
    if availability_filter == 'available':
        books = books.filter(available_copies__gt=0)
    elif availability_filter == 'unavailable':
        books = books.filter(available_copies=0)
    
    categories = Category.objects.all()
    authors = Author.objects.all()
    
    context = {
        'books': books,
        'categories': categories,
        'authors': authors,
        'search_query': search_query,
        'category_filter': category_filter,
        'author_filter': author_filter,
        'availability_filter': availability_filter,
    }
    
    return render(request, 'catalog/book_list.html', context)

