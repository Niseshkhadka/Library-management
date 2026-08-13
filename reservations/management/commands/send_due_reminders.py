"""
Usage:
    python manage.py send_due_reminders
    python manage.py send_due_reminders --start-hours 24 --end-hours 48

Intended to be scheduled to run periodically (e.g. hourly) via cron or
Celery beat:
    0 * * * *  cd /app && python manage.py send_due_reminders

Sends exactly one reminder email per loan (see models.DueDateReminder /
services.send_due_reminders for the idempotency guarantee), so it's safe to
run this more often than the reminder window itself.
"""
from django.core.management.base import BaseCommand

from reservations.services import send_due_reminders


class Command(BaseCommand):
    help = (
        "Email borrowers whose loans are due in the next 24-48 hours "
        "(configurable via --start-hours/--end-hours). Safe to re-run; "
        "already-reminded loans are skipped."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--start-hours",
            type=int,
            default=24,
            help="Start of the reminder window, in hours from now (default: 24).",
        )
        parser.add_argument(
            "--end-hours",
            type=int,
            default=48,
            help="End of the reminder window, in hours from now (default: 48).",
        )

    def handle(self, *args, **options):
        sent = send_due_reminders(
            window_start_hours=options["start_hours"],
            window_end_hours=options["end_hours"],
        )
        self.stdout.write(self.style.SUCCESS(f"Sent {sent} due-date reminder email(s)."))
