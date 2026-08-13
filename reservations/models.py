"""
reservations/models.py

Owns exactly two things: the waitlist entry (Reservation) and a small
idempotency log for due-date reminder emails (DueDateReminder).

Deliberately does NOT duplicate anything the `books` (catalog) or `loans`
apps already own:
  - We don't store copy counts here - `books.Book` is the source of truth
    for how many physical copies exist / are available.
  - We don't store loan history here - `loans.Loan` is the source of truth
    for who currently has a book and when it's due.

We reference books.Book via a lazy string FK ("books.Book") so this app has
no hard import-time dependency on the catalog app's module - just a runtime
dependency once migrations run, which is the normal Django pattern for
cross-app FKs.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"        # waiting in the FIFO queue
        NOTIFIED = "NOTIFIED", "Notified"     # copy held, user has a pickup window
        FULFILLED = "FULFILLED", "Fulfilled"  # user checked the held copy out
        EXPIRED = "EXPIRED", "Expired"        # hold window passed without pickup
        CANCELLED = "CANCELLED", "Cancelled"  # user or staff cancelled it

    # Statuses that still occupy a "slot" in the queue / a hold on a copy.
    ACTIVE_STATUSES = (Status.PENDING, Status.NOTIFIED)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    # Points at the catalog team's Book model. Read-only from this app's
    # perspective except for the availability adjustments made through
    # services.BookGateway (see services.py).
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # created_at (not pk) is the FIFO ordering key. Using a timestamp rather
    # than id keeps ordering correct even after data migrations, bulk loads,
    # or id resequencing.
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    notified_at = models.DateTimeField(null=True, blank=True)
    hold_expires_at = models.DateTimeField(null=True, blank=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Traceability link to the loans app once a hold converts into a real
    # loan. We store the raw id rather than an FK so this app never needs an
    # import-time dependency on loans.Loan.
    fulfilling_loan_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            # One active (PENDING/NOTIFIED) reservation per user per book -
            # stops a single user from stuffing the queue.
            models.UniqueConstraint(
                fields=["user", "book"],
                condition=models.Q(status__in=["PENDING", "NOTIFIED"]),
                name="unique_active_reservation_per_user_book",
            )
        ]
        indexes = [
            # Matches the query shape used everywhere in services.py:
            # "give me this book's queue in FIFO order, filtered by status".
            models.Index(fields=["book", "status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user} -> {self.book} [{self.status}]"

    @property
    def is_active(self) -> bool:
        return self.status in self.ACTIVE_STATUSES

    @property
    def is_hold_expired(self) -> bool:
        return (
            self.status == self.Status.NOTIFIED
            and self.hold_expires_at is not None
            and timezone.now() > self.hold_expires_at
        )


class DueDateReminder(models.Model):
    """
    Idempotency log so `send_due_reminders` never emails the same loan twice,
    even if the command is run more than once inside the same 24-48h window.

    We key on loan_id (a plain int) rather than an FK to loans.Loan, so this
    app has zero *schema* coupling to loans - all it needs to read a loan is
    exposed through services.LoanGateway.
    """
    loan_id = models.PositiveIntegerField(db_index=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["loan_id"], name="unique_due_reminder_per_loan")
        ]

    def __str__(self):
        return f"Reminder sent for loan #{self.loan_id} at {self.sent_at}"
