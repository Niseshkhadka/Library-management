from django.contrib import admin

from .models import DueDateReminder, Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "book", "status", "created_at", "hold_expires_at")
    list_filter = ("status",)
    search_fields = ("user__username", "user__email", "book__title")
    readonly_fields = ("created_at",)


@admin.register(DueDateReminder)
class DueDateReminderAdmin(admin.ModelAdmin):
    list_display = ("id", "loan_id", "sent_at")
    search_fields = ("loan_id",)
