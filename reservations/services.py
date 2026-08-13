"""
reservations/services.py

Single source of truth for reservation business rules. Views, signal
handlers, and management commands all call into these functions rather than
touching Reservation (or books.Book / loans.Loan) directly - that keeps the
FIFO/hold rules auditable in one place and makes them independently testable.

--------------------------------------------------------------------------
CROSS-APP CONTRACT - please confirm the exact names below with whoever owns
`books` and `loans`; the two Gateway classes are the *only* place in this
whole app that assume specific field/method names on their models, so if
their models differ, only this section needs to change.

  books.Book is expected to expose:
    - available_copies : int  (copies free to check out right now)
    optionally:
    - hold_copy() / release_copy() methods, if the catalog app wants to
      encapsulate availability math itself instead of us touching the field.

  loans.Loan is expected to expose:
    - book : FK to books.Book
    - user : FK to settings.AUTH_USER_MODEL
    - due_date : DateTimeField
    - either a Loan.STATUS_RETURNED-style status choice, or a nullable
      returned_date field, to represent "this loan is closed".
--------------------------------------------------------------------------
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from . import emails
from .models import DueDateReminder, Reservation

logger = logging.getLogger(__name__)

# Requirement #3: 48-hour pickup window once a user is notified.
HOLD_WINDOW = timedelta(hours=48)


# ---------------------------------------------------------------------------
# Gateways - thin adapters around teammates' models (see contract above).
# ---------------------------------------------------------------------------

class BookGateway:
    """All reservation <-> catalog interaction goes through here."""

    @staticmethod
    def has_available_copy(book) -> bool:
        return getattr(book, "available_copies", 0) > 0

    @staticmethod
    def place_hold(book) -> None:
        """
        Take one copy out of general availability so it's reserved for the
        notified user for the duration of HOLD_WINDOW.
        """
        if hasattr(book, "hold_copy"):
            book.hold_copy()
        else:
            book.available_copies = max(0, book.available_copies - 1)
            book.save(update_fields=["available_copies"])

    @staticmethod
    def release_hold(book) -> None:
        """Return a held-but-unclaimed copy to general availability."""
        if hasattr(book, "release_copy"):
            book.release_copy()
        else:
            book.available_copies += 1
            book.save(update_fields=["available_copies"])


class LoanGateway:
    """Read-only access to active loans, used only for due-date reminders."""

    @staticmethod
    def get_loans_due_between(start, end):
        from loans.models import Loan  # local import: no hard startup dependency

        qs = Loan.objects.filter(due_date__gte=start, due_date__lte=end)
        if hasattr(Loan, "STATUS_ACTIVE"):
            qs = qs.filter(status=Loan.STATUS_ACTIVE)
        elif hasattr(Loan, "returned_date"):
            qs = qs.filter(returned_date__isnull=True)
        return qs.select_related("user", "book")


# ---------------------------------------------------------------------------
# Reservation lifecycle
# ---------------------------------------------------------------------------

def create_reservation(*, user, book) -> Reservation:
    """
    Requirement #1: only allow a reservation when no physical copy is
    available - otherwise the user should just check the book out directly.
    """
    with transaction.atomic():
        if BookGateway.has_available_copy(book):
            raise ValidationError(
                "This book currently has copies available - check it out "
                "directly instead of reserving it."
            )
        if Reservation.objects.filter(
            user=user, book=book, status__in=Reservation.ACTIVE_STATUSES
        ).exists():
            raise ValidationError("You already have an active reservation for this book.")

        reservation = Reservation.objects.create(
            user=user, book=book, status=Reservation.Status.PENDING
        )
        logger.info("Reservation #%s created for user %s on book #%s", reservation.id, user, book.id)
        return reservation


def cancel_reservation(*, reservation: Reservation, actor) -> Reservation:
    """
    Cancel a PENDING or NOTIFIED reservation. If the reservation was
    NOTIFIED (i.e. actively holding a copy), releasing it must immediately
    advance the queue so the held copy doesn't sit idle.
    """
    if reservation.user_id != actor.id and not getattr(actor, "is_staff", False):
        raise PermissionError("You may only cancel your own reservations.")
    if not reservation.is_active:
        raise ValidationError("This reservation is no longer active and can't be cancelled.")

    with transaction.atomic():
        was_notified = reservation.status == Reservation.Status.NOTIFIED
        reservation.status = Reservation.Status.CANCELLED
        reservation.cancelled_at = timezone.now()
        reservation.save(update_fields=["status", "cancelled_at"])

        if was_notified:
            BookGateway.release_hold(reservation.book)
            _advance_queue(reservation.book)

    logger.info("Reservation #%s cancelled by user %s", reservation.id, actor)
    return reservation


def mark_fulfilled(reservation: Reservation, loan_id: int) -> Reservation:
    """
    Call this once the notified user actually checks the held book out
    (e.g. from a signal on loans.Loan creation matching a NOTIFIED
    reservation for that user+book). Closes the loop cleanly.
    """
    reservation.status = Reservation.Status.FULFILLED
    reservation.fulfilled_at = timezone.now()
    reservation.fulfilling_loan_id = loan_id
    reservation.save(update_fields=["status", "fulfilled_at", "fulfilling_loan_id"])
    return reservation


def queue_position(reservation: Reservation) -> int:
    """1-indexed position of a PENDING reservation among others for the same book."""
    if reservation.status != Reservation.Status.PENDING:
        return 0
    return (
        Reservation.objects.filter(
            book=reservation.book,
            status=Reservation.Status.PENDING,
            created_at__lt=reservation.created_at,
        ).count()
        + 1
    )


# ---------------------------------------------------------------------------
# Requirement #2 + #3: FIFO queue advancement + availability notification
# ---------------------------------------------------------------------------

def process_book_return(book) -> Optional[Reservation]:
    """
    Entry point called from signals.py whenever a copy becomes available
    again (a Loan is marked returned). Notifies the longest-waiting PENDING
    reservation and places a 48h hold. Returns the notified Reservation, or
    None if nobody is waiting (copy just stays generally available).
    """
    with transaction.atomic():
        return _advance_queue(book)


def _advance_queue(book) -> Optional[Reservation]:
    """
    Strict FIFO pop: oldest PENDING reservation for this book wins the copy.
    select_for_update + the surrounding transaction.atomic() in every caller
    prevents two returns/expirations racing to hand the same copy to two
    different people.
    """
    next_in_line = (
        Reservation.objects.select_for_update()
        .filter(book=book, status=Reservation.Status.PENDING)
        .order_by("created_at")
        .first()
    )
    if next_in_line is None:
        return None
    if not BookGateway.has_available_copy(book):
        return None  # defensive: nothing to hand out right now

    BookGateway.place_hold(book)
    now = timezone.now()
    next_in_line.status = Reservation.Status.NOTIFIED
    next_in_line.notified_at = now
    next_in_line.hold_expires_at = now + HOLD_WINDOW
    next_in_line.save(update_fields=["status", "notified_at", "hold_expires_at"])

    emails.send_reservation_available_email(next_in_line)
    logger.info("Reservation #%s notified, hold expires %s", next_in_line.id, next_in_line.hold_expires_at)
    return next_in_line


def expire_stale_holds() -> int:
    """
    Periodic sweep (management command `expire_reservation_holds`, run every
    15-30 min via cron/Celery beat) that expires holds nobody picked up
    within HOLD_WINDOW and passes the copy on to the next person in line.
    This is what makes the 48h window in requirement #3 actually enforced -
    signals alone can't react to the mere passage of time.
    """
    expired_count = 0
    stale = Reservation.objects.filter(
        status=Reservation.Status.NOTIFIED, hold_expires_at__lt=timezone.now()
    )
    for reservation in stale:
        with transaction.atomic():
            reservation.status = Reservation.Status.EXPIRED
            reservation.save(update_fields=["status"])
            BookGateway.release_hold(reservation.book)
            _advance_queue(reservation.book)
        expired_count += 1
        logger.info("Reservation #%s expired (hold window passed)", reservation.id)
    return expired_count


# ---------------------------------------------------------------------------
# Requirement #4: due-date reminders
# ---------------------------------------------------------------------------

def send_due_reminders(window_start_hours: int = 24, window_end_hours: int = 48) -> int:
    """
    Core logic behind the `send_due_reminders` management command. Finds
    active loans due between window_start_hours and window_end_hours from
    now, and emails each borrower once (idempotent via DueDateReminder).
    """
    now = timezone.now()
    window_start = now + timedelta(hours=window_start_hours)
    window_end = now + timedelta(hours=window_end_hours)

    loans = list(LoanGateway.get_loans_due_between(window_start, window_end))
    already_reminded = set(
        DueDateReminder.objects.filter(
            loan_id__in=[loan.id for loan in loans]
        ).values_list("loan_id", flat=True)
    )

    sent = 0
    for loan in loans:
        if loan.id in already_reminded:
            continue
        try:
            emails.send_due_date_reminder_email(loan)
            DueDateReminder.objects.create(loan_id=loan.id)
            sent += 1
        except Exception:
            logger.exception("Failed to send due-date reminder for loan #%s", loan.id)
    return sent
