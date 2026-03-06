from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username", "email",
        "rgpd_accepte", "rgpd_date_acceptation",
        "is_staff", "is_active",
        "last_login", "date_joined",
    )
    list_filter = ("is_staff", "is_active", "rgpd_accepte", "groups")
    search_fields = ("username", "email")
    ordering = ("-date_joined",)

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("RGPD", {"fields": ("rgpd_accepte", "rgpd_date_acceptation")}),
    )
