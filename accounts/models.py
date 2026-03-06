from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    rgpd_accepte = models.BooleanField(default=False)
    rgpd_date_acceptation = models.DateTimeField(null=True, blank=True)

    # “statut” simple (soft delete / désactivation)
    is_active = models.BooleanField(default=True)  # déjà présent dans AbstractUser

    def accept_rgpd(self):
        self.rgpd_accepte = True
        self.rgpd_date_acceptation = timezone.now()
        self.save(update_fields=["rgpd_accepte", "rgpd_date_acceptation"])