from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q

class Menu(models.Model):
    titre = models.CharField(max_length=80)
    ordre = models.PositiveIntegerField(default=0)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.titre


class PageInformation(models.Model):
    STATUT_CHOICES = [
        ("brouillon", "Brouillon"),
        ("publie", "Publié"),
        ("archive", "Archivé"),
    ]

    titre = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    contenu = models.TextField()
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="brouillon")
    date_publication = models.DateTimeField(null=True, blank=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titre


class MenuEntree(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="entrees")
    libelle = models.CharField(max_length=80)
    ordre_affichage = models.PositiveIntegerField(default=0)

    page = models.ForeignKey(PageInformation, null=True, blank=True, on_delete=models.SET_NULL)
    url_externe = models.URLField(null=True, blank=True)

    def clean(self):
        # XOR : exactement un des deux doit être rempli
        if bool(self.page) == bool(self.url_externe):
            raise ValidationError("Une entrée doit référencer une page OU une url externe (pas les deux, pas aucun).")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(page__isnull=False) & Q(url_externe__isnull=True)) |
                    (Q(page__isnull=True) & Q(url_externe__isnull=False))
                ),
                name="menuentree_page_xor_url",
            )
        ]

    def __str__(self):
        return f"{self.menu} - {self.libelle}"