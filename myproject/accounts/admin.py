from django.contrib import admin
from .models import Alumni, Event, EventRegistration, Job


@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):

    list_display = (
        "register_number",
        "full_name",
        "date_of_birth",
        "email",
        "phone",
        "batch",
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "event_date",
        "start_time",
        "is_online",
        "capacity",
        "seats_available_display",
    )
    list_filter = ("category", "is_online", "event_date")
    search_fields = ("title", "chief_guest", "featured_alumni", "location")
    fieldsets = (
        ("Event", {"fields": ("title", "category", "description", "agenda")} ),
        ("Schedule", {"fields": ("event_date", "start_time", "end_time")} ),
        ("Venue & capacity", {"fields": ("is_online", "location", "meeting_link", "capacity")} ),
        ("People", {"fields": ("chief_guest", "chief_guest_title", "chief_guest_bio", "featured_alumni", "featured_alumni_role")} ),
    )

    @admin.display(description="Seats left")
    def seats_available_display(self, event):
        return event.seats_available


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ("event", "full_name", "register_number", "email", "guests", "registered_at")
    list_filter = ("event", "attendance", "lunch_required")
    search_fields = ("full_name", "register_number", "email")
    readonly_fields = ("registered_at",)

    search_fields = (
        "register_number",
        "full_name",
        "email",
    )



@admin.register(Job)
class JobAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "company",
        "location",
        "category",
        "experience",
        "job_type",
        "last_date",
        "is_active",
    )

    list_filter = (
        "category",
        "experience",
        "job_type",
        "is_active",
        "company",
    )

    search_fields = (
        "title",
        "company",
        "location",
        "skills",
        "description",
    )

    list_editable = (
        "is_active",
    )

    ordering = (
        "-created_at",
    )



