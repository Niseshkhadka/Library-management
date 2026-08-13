"""
reservations/signals.py

Bridges `loans` app events into the waitlist engine. This is the ONLY file
in this app that subscribes to another app's model signals - keep it that
way so the coupling surface stays easy to find and review.

Integration contract with loans (confirm with the loans owner, adjust
`_loan_is_returned` below if their actual field/status names differ):
  - loans.Loan has a `book` FK to books.Book
  - a "book was returned" event is representable as either:
      (a) Loan.status transitioning to a Loan.STATUS_RETURNED-style value, or
      (b) Loan.returned_date being set (previously null)

We use pre_save + post_save together (rather than post_save alone) so we
only fire when a loan actually *transitions into* returned on this save,
not on every subsequent save of an already-returned loan.
"""
import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from . import services

logger = logging.getLogger(__name__)

try:
    from loans.models import Loan
except ImportError:  # loans app not installed yet, e.g. isolated unit tests
    Loan = None


def _loan_is_returned(loan) -> bool:
    if hasattr(loan, "status") and hasattr(loan.__class__, "STATUS_RETURNED"):
        return loan.status == loan.__class__.STATUS_RETURNED
    return bool(getattr(loan, "returned_date", None))


if Loan is not None:

    @receiver(pre_save, sender=Loan)
    def _capture_previous_return_state(sender, instance, **kwargs):
        """Stash whether this loan was ALREADY returned before this save,
        so post_save can detect a genuine not-returned -> returned edge."""
        if instance.pk:
            try:
                previous = sender.objects.get(pk=instance.pk)
                instance._was_returned = _loan_is_returned(previous)
            except sender.DoesNotExist:
                instance._was_returned = False
        else:
            instance._was_returned = False

    @receiver(post_save, sender=Loan)
    def handle_loan_saved(sender, instance, created, **kwargs):
        if created:
            return  # a brand-new loan is not a return event

        was_returned = getattr(instance, "_was_returned", False)
        is_returned_now = _loan_is_returned(instance)

        if is_returned_now and not was_returned:
            logger.info(
                "Loan #%s returned - advancing reservation queue for book #%s",
                instance.pk,
                instance.book_id,
            )
            services.process_book_return(instance.book)
else:
    logger.warning("loans app not found - reservation queue will not auto-advance on returns")
