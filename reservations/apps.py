from django.apps import AppConfig


class ReservationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reservations"

    def ready(self):
        # Importing signals here (rather than at module top-level in
        # models.py) is the Django-recommended place to wire up receivers,
        # since it runs once all apps are loaded.
        from . import signals  # noqa: F401
