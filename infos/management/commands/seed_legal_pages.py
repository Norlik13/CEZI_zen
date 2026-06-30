from django.core.management.base import BaseCommand
from django.utils import timezone
from infos.models import PageInformation

MENTIONS = """\
## Éditeur du site
CESIZen

-Hébergement
Application hébergée en local (environnement de développement)

-Propriété intellectuelle
Toute reproduction non autorisée est interdite.

-Limitation de responsabilité
Les informations proposées n’ont pas vocation à remplacer un avis médical. En cas de détresse,
contactez un professionnel de santé ou les services d’urgence.
"""

PRIVACY = """\
-Responsable du traitement
Responsable : Ministère de la Santé et de la Prévention

-Données traitées
- Données de compte : identifiant, email, mot de passe (haché)
- Données de suivi : entrées du tracker d’émotions (émotion choisie, intensité optionnelle, commentaire optionnel, date)

-Finalités
- Création et gestion du compte utilisateur
- Utilisation du tracker d’émotions et génération de rapports par période
- Sécurisation du service (authentification, prévention d’accès non autorisés)

-Base légale
- Exécution du service (compte + fonctionnalités)
- Consentement : acceptation RGPD lors de la création du compte (tracé par date)

-Destinataires
- Équipe projet (administration technique).
Aucun partage à des tiers commerciaux.

-Durée de conservation
- Compte : jusqu’à suppression du compte
- Entrées tracker : jusqu’à suppression par l’utilisateur ou suppression du compte
- Données techniques (logs) : durée limitée selon besoin de sécurité (ex : 30 jours)

-Sécurité
- Mot de passe haché
- Accès réservé (authentification)
- Droits d’accès limités aux administrateurs

-Vos droits
Vous disposez des droits d’accès, rectification, effacement, limitation, opposition et portabilité.
Vous pouvez également introduire une réclamation auprès de la CNIL.

-Cookies
L’application ne dépose pas de cookies publicitaires. Si des cookies de mesure d’audience sont ajoutés,
ils seront configurés conformément aux règles applicables (information et, si nécessaire, consentement).
"""

CONTACT=""" \
-Email: contact@cesizen.fr
-Adresse: 14 Av. Duquesne, 75350 Paris
-Telephone: 01 40 56 60 00
"""


class Command(BaseCommand):
    help = "Crée les pages Mentions légales et Données personnelles (RGPD) si elles n'existent pas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Supprime le référentiel existant avant d'insérer.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            mention_legale = PageInformation.objects.filter(slug="mentions-legales")
            if mention_legale:
                mention_legale.delete()
            donnees_personnelles = PageInformation.objects.filter(slug="donnees-personnelles")
            if donnees_personnelles:
                donnees_personnelles.delete()
            contact = PageInformation.objects.filter(slug="contact")
            if contact:
                contact.delete()
            self.stdout.write(self.style.WARNING("Référentiel existant supprimé."))

        now = timezone.now()

        PageInformation.objects.get_or_create(
            slug="mentions-legales",
            defaults={
                "titre": "Mentions légales",
                "contenu": MENTIONS,
                "statut": "publie",
                "date_publication": now,
            },
        )

        PageInformation.objects.get_or_create(
            slug="donnees-personnelles",
            defaults={
                "titre": "Données personnelles",
                "contenu": PRIVACY,
                "statut": "publie",
                "date_publication": now,
            },
        )

        PageInformation.objects.get_or_create(
            slug="contact",
            defaults={
                "titre": "Contact",
                "contenu": CONTACT,
                "statut": "publie",
                "date_publication": now,
            },
        )

        self.stdout.write(self.style.SUCCESS("Pages légales créées/vérifiées avec succès."))
