from django.contrib import admin
from .models import Alumni


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

    search_fields = (
        "register_number",
        "full_name",
        "email",
    )



