"""
Usage:
    python manage.py expire_reservation_holds

Not explicitly requested in the spec, but required to actually ENFORCE the
48-hour hold window from requirement #3: a signal only fires on book
returns, it can't fire on "48 hours have now passed". This sweep is what
expires abandoned holds and passes the copy to the next person in the FIFO
queue. Schedule it to run every 15-30 minutes via cron or Celery beat:
    */15 * * * *  cd /app && python manage.py expire_reservation_holds
"""
from django.core.management.base import BaseCommand

from reservations.services import expire_stale_holds


class Command(BaseCommand):
    help = (
        "Expire reservation holds whose 48h pickup window has passed and "
        "advance the FIFO queue to the next waiting user."
    )

    def handle(self, *args, **options):
        count = expire_stale_holds()
        self.stdout.write(self.style.SUCCESS(f"Expired {count} stale reservation hold(s)."))
