from django.contrib import admin
from .models import Menu, MenuEntree, PageInformation


class MenuEntreeInline(admin.TabularInline):
    model = MenuEntree
    extra = 1
    fields = ("libelle", "ordre_affichage", "page", "url_externe")
    ordering = ("ordre_affichage",)


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("titre", "ordre", "actif")
    list_filter = ("actif",)
    search_fields = ("titre",)
    ordering = ("ordre", "titre")
    inlines = [MenuEntreeInline]


@admin.register(PageInformation)
class PageInformationAdmin(admin.ModelAdmin):
    list_display = ("titre", "slug", "statut", "date_publication", "date_mise_a_jour")
    list_filter = ("statut",)
    search_fields = ("titre", "slug", "contenu")
    prepopulated_fields = {"slug": ("titre",)}
    ordering = ("-date_mise_a_jour",)


@admin.register(MenuEntree)
class MenuEntreeAdmin(admin.ModelAdmin):
    list_display = ("menu", "libelle", "ordre_affichage", "page", "url_externe")
    list_filter = ("menu",)
    search_fields = ("libelle", "url_externe", "page__titre")
    ordering = ("menu__ordre", "ordre_affichage")
