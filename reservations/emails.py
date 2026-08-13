"""
reservations/emails.py

Keeps all "how do we send this email" details (templates, subject lines,
from-address) out of services.py, so the business logic stays readable and
the email format can change without touching queue logic.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_reservation_available_email(reservation) -> None:
    """Notify the next-in-line user that their held copy is ready (see
    services.process_book_return / services._advance_queue)."""
    user, book = reservation.user, reservation.book
    context = {"user": user, "book": book, "hold_expires_at": reservation.hold_expires_at}
    subject = f'"{book.title}" is ready for pickup'
    message = render_to_string("reservations/email/available.txt", context)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)


def send_due_date_reminder_email(loan) -> None:
    """Remind a borrower their loan is due soon (see services.send_due_reminders)."""
    user, book = loan.user, loan.book
    context = {"user": user, "book": book, "due_date": loan.due_date}
    subject = f'Reminder: "{book.title}" is due soon'
    message = render_to_string("reservations/email/due_reminder.txt", context)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
