"""
reservations/views.py

Thin HTTP layer: parse the request, call services.py, translate the result
(or raised exception) into a response. No queue/business logic lives here.
"""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from books.models import Book  # catalog app - read-only lookup only
from . import services
from .models import Reservation


def _wants_json(request) -> bool:
    return request.headers.get("Accept") == "application/json" or request.headers.get(
        "X-Requested-With"
    ) == "XMLHttpRequest"


@login_required
@require_http_methods(["POST"])
def create_reservation_view(request, book_id):
    """POST /reservations/books/<book_id>/reserve/"""
    book = get_object_or_404(Book, pk=book_id)
    try:
        reservation = services.create_reservation(user=request.user, book=book)
    except ValidationError as exc:
        message = exc.messages[0] if hasattr(exc, "messages") else str(exc)
        if _wants_json(request):
            return JsonResponse({"error": message}, status=400)
        return render(request, "reservations/error.html", {"message": message}, status=400)

    if _wants_json(request):
        return JsonResponse(
            {
                "id": reservation.id,
                "status": reservation.status,
                "queue_position": services.queue_position(reservation),
            },
            status=201,
        )
    return redirect("reservations:my_reservations")


@login_required
@require_http_methods(["POST"])
def cancel_reservation_view(request, pk):
    """POST /reservations/<pk>/cancel/"""
    reservation = get_object_or_404(Reservation, pk=pk)
    try:
        services.cancel_reservation(reservation=reservation, actor=request.user)
    except PermissionError as exc:
        if _wants_json(request):
            return JsonResponse({"error": str(exc)}, status=403)
        return render(request, "reservations/error.html", {"message": str(exc)}, status=403)
    except ValidationError as exc:
        message = exc.messages[0] if hasattr(exc, "messages") else str(exc)
        if _wants_json(request):
            return JsonResponse({"error": message}, status=400)
        return render(request, "reservations/error.html", {"message": message}, status=400)

    if _wants_json(request):
        return JsonResponse({"id": reservation.id, "status": reservation.status})
    return redirect("reservations:my_reservations")


@login_required
@require_http_methods(["GET"])
def my_reservations_view(request):
    """GET /reservations/mine/ - a user's own reservation history + live queue positions."""
    reservations = (
        Reservation.objects.filter(user=request.user)
        .select_related("book")
        .order_by("-created_at")
    )
    context = {
        "reservations": [
            {"reservation": r, "queue_position": services.queue_position(r)}
            for r in reservations
        ]
    }
    return render(request, "reservations/my_reservations.html", context)
