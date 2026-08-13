from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthorViewSet, CategoryViewSet, BookViewSet, book_list_page, book_detail_page, add_book_page

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'books', BookViewSet, basename='book')

urlpatterns = [
    path('books-page/', book_list_page, name='book-list-page'),
    path('books-page/<int:pk>/', book_detail_page, name='book-detail-page'),
    path('books-page/add/', add_book_page, name='add-book-page'),
    path('', include(router.urls)),
]