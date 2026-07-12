from django.contrib import admin

from ptas.models import PublicTransitAgency


@admin.register(PublicTransitAgency)
class PublicTransitAgencyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "color", "owner")
    search_fields = ("id", "name", "owner__email")
