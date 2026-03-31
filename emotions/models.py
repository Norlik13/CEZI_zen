from django.conf import settings
from django.db import models

class EmotionBase(models.Model):
    libelle = models.CharField(max_length=60, unique=True)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.libelle


class Emotion(models.Model):
    base = models.ForeignKey(EmotionBase, on_delete=models.CASCADE, related_name="emotions")
    libelle = models.CharField(max_length=60)
    actif = models.BooleanField(default=True)

    class Meta:
        unique_together = ("base", "libelle")

    def __str__(self):
        return f"{self.base} / {self.libelle}"


class TrackerItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tracker_items")
    emotion = models.ForeignKey(Emotion, on_delete=models.PROTECT)
    date_saisie = models.DateTimeField(auto_now_add=True)
    intensite = models.PositiveSmallIntegerField(null=True, blank=True)
    commentaire = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user} - {self.emotion} ({self.date_saisie:%Y-%m-%d})"