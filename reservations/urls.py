"""
reservations/urls.py

Mount this in the project's root urls.py with:
    path("reservations/", include("reservations.urls")),
"""
from django.urls import path

from . import views

app_name = "reservations"

urlpatterns = [
    # Nested under books/ since a reservation is always "reserve THIS book" -
    # keeps the book_id in the URL rather than a form field.
    path("books/<int:book_id>/reserve/", views.create_reservation_view, name="create"),
    path("<int:pk>/cancel/", views.cancel_reservation_view, name="cancel"),
    path("mine/", views.my_reservations_view, name="my_reservations"),
]
