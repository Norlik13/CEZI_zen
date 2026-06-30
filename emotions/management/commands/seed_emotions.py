from django.core.management.base import BaseCommand
from emotions.models import EmotionBase, Emotion

REFERENTIEL = {
    "Joie": [
        "Fierté", "Contentement", "Enchantement",
        "Excitation", "Émerveillement", "Gratitude",
    ],
    "Colère": [
        "Frustration", "Irritation", "Rage",
        "Ressentiment", "Agacement", "Hostilité",
    ],
    "Peur": [
        "Inquiétude", "Anxiété", "Terreur",
        "Appréhension", "Panique", "Crainte",
    ],
    "Tristesse": [
        "Chagrin", "Mélancolie", "Abattement",
        "Désespoir", "Solitude", "Dépression",
    ],
    "Surprise": [
        "Stupéfaction", "Étonnement", "Sidération",
        "Confusion", "Incrédulité", "Émerveillement",
    ],
    "Dégoût": [
        "Répulsion", "Déplaisir", "Nausée",
        "Dédain", "Horreur", "Dégoût profond",
    ],
}


class Command(BaseCommand):
    help = "Seed du référentiel d'émotions (N1 -> N2) pour le tracker."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Supprime le référentiel existant avant d'insérer.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            Emotion.objects.all().delete()
            EmotionBase.objects.all().delete()
            self.stdout.write(self.style.WARNING("Référentiel existant supprimé."))

        created_bases = 0
        created_emotions = 0

        for base_label, emotions in REFERENTIEL.items():
            base, base_created = EmotionBase.objects.get_or_create(
                libelle=base_label,
                defaults={"actif": True},
            )
            if base_created:
                created_bases += 1

            for emo_label in emotions:
                _, emo_created = Emotion.objects.get_or_create(
                    base=base,
                    libelle=emo_label,
                    defaults={"actif": True},
                )
                if emo_created:
                    created_emotions += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeding terminé. Bases créées: {created_bases}, Émotions créées: {created_emotions}"
        ))
