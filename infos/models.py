from django.db import models


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
