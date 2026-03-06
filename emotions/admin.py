from django.contrib import admin
from .models import EmotionBase, Emotion, TrackerItem


class EmotionInline(admin.TabularInline):
    model = Emotion
    extra = 1
    fields = ("libelle", "actif")
    ordering = ("libelle",)


@admin.register(EmotionBase)
class EmotionBaseAdmin(admin.ModelAdmin):
    list_display = ("libelle", "actif")
    list_filter = ("actif",)
    search_fields = ("libelle",)
    ordering = ("libelle",)
    inlines = [EmotionInline]


@admin.register(Emotion)
class EmotionAdmin(admin.ModelAdmin):
    list_display = ("base", "libelle", "actif")
    list_filter = ("base", "actif")
    search_fields = ("libelle", "base__libelle")
    ordering = ("base__libelle", "libelle")


@admin.register(TrackerItem)
class TrackerItemAdmin(admin.ModelAdmin):
    list_display = ("user", "get_base", "emotion", "intensite", "date_saisie")
    list_filter = ("emotion__base", "emotion", "date_saisie")
    search_fields = ("user__username", "user__email", "commentaire", "emotion__libelle")
    ordering = ("-date_saisie",)
    autocomplete_fields = ("user", "emotion")

    @admin.display(description="Émotion de base (N1)")
    def get_base(self, obj):
        return obj.emotion.base.libelle
