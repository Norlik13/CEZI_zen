from django.contrib import admin
from .models import PageInformation


@admin.register(PageInformation)
class PageInformationAdmin(admin.ModelAdmin):
    list_display = ("titre", "slug", "statut", "date_publication", "date_mise_a_jour")
    list_filter = ("statut",)
    search_fields = ("titre", "slug", "contenu")
    prepopulated_fields = {"slug": ("titre",)}
    ordering = ("-date_mise_a_jour",)
