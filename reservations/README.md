# reservations

Handles book reservations, the FIFO waitlist queue, availability-hold
notifications, and due-date reminder emails for the Library Management
System.

## Wiring it into the project

1. Add to `INSTALLED_APPS` **after** `books` and `loans`:
   ```python
   INSTALLED_APPS = [
       ...
       "books",
       "loans",
       "reservations",
   ]
   ```
2. Mount the URLs in the project's root `urls.py`:
   ```python
   path("reservations/", include("reservations.urls")),
   ```
3. Generate and run migrations:
   ```bash
   python manage.py makemigrations reservations
   python manage.py migrate
   ```
4. Schedule the two management commands (cron or Celery beat):
   ```
   0 * * * *     python manage.py send_due_reminders        # hourly
   */15 * * * *  python manage.py expire_reservation_holds   # every 15 min
   ```
5. Set `DEFAULT_FROM_EMAIL` and an `EMAIL_BACKEND` in settings (console
   backend is fine for dev).

## How this app touches `books` and `loans`

This app deliberately never imports `books.Book` or `loans.Loan` logic
directly outside of two small adapter classes in `services.py`:
`BookGateway` and `LoanGateway`. If the catalog/loan owners' actual field
names differ from the assumptions documented at the top of `services.py`
(`available_copies`, `due_date`, a returned-state field), that file is the
**only** place that needs to change - models.py, signals.py, views.py, and
the management commands are all written against `services.py`, not against
the other apps' models.

- **books**: read `available_copies` to decide whether a reservation is
  allowed; increment/decrement it (or call `hold_copy()`/`release_copy()`
  if the catalog app provides them) to place/release a 48h hold.
- **loans**: `signals.py` listens for a Loan transitioning into "returned"
  and calls `services.process_book_return(book)` to advance the queue.
  `services.LoanGateway` reads upcoming due dates for reminder emails.
  When the loans app creates a new Loan for a user with a `NOTIFIED`
  reservation on that book, it should call
  `services.mark_fulfilled(reservation, loan.id)` to close the loop -
  that's the one call the loans team needs to add on their end.

## Status lifecycle

```
PENDING --(book returned, next in line)--> NOTIFIED --(user checks it out)--> FULFILLED
   |                                           |
   |--(user/staff cancels)--> CANCELLED        |--(48h passes)--> EXPIRED --> queue advances
                                                |--(user/staff cancels)--> CANCELLED --> queue advances
```

## Files

| File | Responsibility |
|---|---|
| `models.py` | `Reservation`, `DueDateReminder` |
| `services.py` | All business rules: create/cancel, FIFO advancement, hold expiry, due reminders |
| `signals.py` | Loan-returned -> `services.process_book_return` bridge |
| `emails.py` | Email formatting/sending, isolated from business logic |
| `views.py` / `urls.py` | Create / cancel / list reservations |
| `management/commands/send_due_reminders.py` | Requirement #4 |
| `management/commands/expire_reservation_holds.py` | Enforces the 48h window from requirement #3 |
