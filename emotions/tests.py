from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from infos.models import PageInformation

from .forms import TrackerItemForm
from .models import Emotion, EmotionBase, TrackerItem
from .views import _period_start

User = get_user_model()


class EmotionsModelTests(TestCase):
    def setUp(self):
        self.base = EmotionBase.objects.create(libelle="Joie", actif=True)
        self.emotion = Emotion.objects.create(base=self.base, libelle="Gratitude", actif=True)
        self.user = User.objects.create_user(username="alice", password="pass1234")

    def test_emotion_base_str_returns_libelle(self):
        self.assertEqual(str(self.base), "Joie")

    def test_emotion_str_returns_base_and_label(self):
        self.assertEqual(str(self.emotion), "Joie / Gratitude")

    def test_emotion_unique_together_on_base_and_libelle(self):
        with self.assertRaises(IntegrityError):
            Emotion.objects.create(base=self.base, libelle="Gratitude", actif=True)

    def test_tracker_item_str_contains_user_emotion_and_date(self):
        item = TrackerItem.objects.create(user=self.user, emotion=self.emotion, intensite=8)
        as_text = str(item)

        self.assertIn("alice", as_text)
        self.assertIn("Gratitude", as_text)

    def test_tracker_item_validators_reject_intensity_above_10(self):
        item = TrackerItem(user=self.user, emotion=self.emotion, intensite=11)

        with self.assertRaisesMessage(Exception, "Ensure this value is less than or equal to 10"):
            item.full_clean()


class TrackerItemFormTests(TestCase):
    def setUp(self):
        self.active_base = EmotionBase.objects.create(libelle="Joie", actif=True)
        self.inactive_base = EmotionBase.objects.create(libelle="Peur", actif=False)
        self.active_emotion = Emotion.objects.create(base=self.active_base, libelle="Fierte", actif=True)
        self.inactive_emotion = Emotion.objects.create(base=self.active_base, libelle="Rage", actif=False)
        self.inactive_base_emotion = Emotion.objects.create(base=self.inactive_base, libelle="Anxiete", actif=True)

    def test_tracker_form_exposes_only_active_emotions_from_active_bases(self):
        form = TrackerItemForm()

        self.assertEqual(list(form.fields["emotion"].queryset), [self.active_emotion])

    def test_tracker_form_sets_intensity_widget_attributes(self):
        form = TrackerItemForm()
        attrs = form.fields["intensite"].widget.attrs

        self.assertEqual(attrs.get("min"), 0)
        self.assertEqual(attrs.get("max"), 10)
        self.assertEqual(attrs.get("step"), 1)


class EmotionsPeriodHelperTests(TestCase):
    def test_period_start_all_returns_none_start(self):
        period, start = _period_start("all")

        self.assertEqual(period, "all")
        self.assertIsNone(start)

    def test_period_start_legacy_30d_maps_to_month(self):
        period, start = _period_start("30d")

        self.assertEqual(period, "month")
        self.assertEqual(start.day, 1)

    def test_period_start_unknown_falls_back_to_month(self):
        period, start = _period_start("unknown")

        self.assertEqual(period, "month")
        self.assertEqual(start.day, 1)


class TrackerViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="john", password="pass1234")
        self.other_user = User.objects.create_user(username="mary", password="pass1234")

        base = EmotionBase.objects.create(libelle="Joie", actif=True)
        self.emotion = Emotion.objects.create(base=base, libelle="Contentement", actif=True)

        self.user_item = TrackerItem.objects.create(
            user=self.user,
            emotion=self.emotion,
            intensite=7,
            commentaire="bon jour",
        )
        self.other_item = TrackerItem.objects.create(
            user=self.other_user,
            emotion=self.emotion,
            intensite=3,
            commentaire="autre user",
        )

    def test_tracker_views_redirect_when_anonymous(self):
        urls = [
            reverse("tracker_list"),
            reverse("tracker_add"),
            reverse("tracker_edit", args=[self.user_item.pk]),
            reverse("tracker_delete", args=[self.user_item.pk]),
            reverse("tracker_report"),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(f"{reverse('login')}?next="))

    def test_tracker_list_shows_only_current_user_items(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("tracker_list"))

        self.assertEqual(response.status_code, 200)
        items = list(response.context["items"])
        self.assertIn(self.user_item, items)
        self.assertNotIn(self.other_item, items)

    def test_tracker_list_applies_period_filter(self):
        self.client.force_login(self.user)

        old_item = TrackerItem.objects.create(
            user=self.user,
            emotion=self.emotion,
            intensite=4,
            commentaire="ancien",
        )
        TrackerItem.objects.filter(pk=old_item.pk).update(
            date_saisie=timezone.now() - timedelta(days=45)
        )

        response = self.client.get(reverse("tracker_list"), {"period": "month"})

        items = list(response.context["items"])
        self.assertIn(self.user_item, items)
        self.assertNotIn(old_item, items)

    def test_tracker_create_creates_item_for_logged_user(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("tracker_add"),
            data={"emotion": self.emotion.pk, "intensite": 5, "commentaire": "ok"},
        )

        self.assertRedirects(response, reverse("tracker_list"))
        self.assertTrue(
            TrackerItem.objects.filter(user=self.user, intensite=5, commentaire="ok").exists()
        )

    def test_tracker_update_allows_owner(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("tracker_edit", args=[self.user_item.pk]),
            data={"emotion": self.emotion.pk, "intensite": 9, "commentaire": "maj"},
        )

        self.assertRedirects(response, reverse("tracker_list"))
        self.user_item.refresh_from_db()
        self.assertEqual(self.user_item.intensite, 9)
        self.assertEqual(self.user_item.commentaire, "maj")

    def test_tracker_update_denies_non_owner(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("tracker_edit", args=[self.other_item.pk]))

        self.assertEqual(response.status_code, 404)

    def test_tracker_delete_allows_owner(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("tracker_delete", args=[self.user_item.pk]))

        self.assertRedirects(response, reverse("tracker_list"))
        self.assertFalse(TrackerItem.objects.filter(pk=self.user_item.pk).exists())

    def test_tracker_report_returns_grouped_stats(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("tracker_report"))

        self.assertEqual(response.status_code, 200)
        by_base = list(response.context["by_base"])
        by_emotion = list(response.context["by_emotion"])

        self.assertEqual(by_base[0]["emotion__base__libelle"], "Joie")
        self.assertEqual(by_base[0]["nb"], 1)
        self.assertAlmostEqual(float(by_base[0]["avg_int"]), 7.0)
        self.assertEqual(by_emotion[0]["emotion__libelle"], "Contentement")


class EmotionsAdminViewsTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass1234",
            is_staff=True,
        )
        self.group_admin_user = User.objects.create_user(
            username="group_admin",
            email="group_admin@example.com",
            password="pass1234",
        )
        admin_group = Group.objects.create(name="ADMIN")
        self.group_admin_user.groups.add(admin_group)

        self.regular_user = User.objects.create_user(
            username="regular", email="regular@example.com", password="pass1234"
        )

        self.base = EmotionBase.objects.create(libelle="Peur", actif=True)
        self.emo = Emotion.objects.create(base=self.base, libelle="Anxiete", actif=True)

    def test_admin_reference_pages_require_admin_permissions(self):
        response = self.client.get(reverse("base_list"))
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.regular_user)
        response = self.client.get(reverse("base_list"))
        self.assertEqual(response.status_code, 302)

    def test_admin_reference_pages_accessible_to_staff_and_group_admin(self):
        self.client.force_login(self.admin_user)
        self.assertEqual(self.client.get(reverse("base_list")).status_code, 200)
        self.client.logout()

        self.client.force_login(self.group_admin_user)
        self.assertEqual(self.client.get(reverse("emotion_list")).status_code, 200)

    def test_base_crud_create_update_delete(self):
        self.client.force_login(self.admin_user)

        create_response = self.client.post(
            reverse("base_add"),
            data={"libelle": "Colere", "actif": "on"},
        )
        self.assertRedirects(create_response, reverse("base_list"))
        created = EmotionBase.objects.get(libelle="Colere")

        update_response = self.client.post(
            reverse("base_edit", args=[created.pk]),
            data={"libelle": "Colere MAJ", "actif": "on"},
        )
        self.assertRedirects(update_response, reverse("base_list"))
        created.refresh_from_db()
        self.assertEqual(created.libelle, "Colere MAJ")

        delete_response = self.client.post(reverse("base_delete", args=[created.pk]))
        self.assertRedirects(delete_response, reverse("base_list"))
        self.assertFalse(EmotionBase.objects.filter(pk=created.pk).exists())

    def test_emotion_crud_and_filtering(self):
        self.client.force_login(self.admin_user)

        create_response = self.client.post(
            reverse("emotion_add"),
            data={"base": self.base.pk, "libelle": "Panique", "actif": "on"},
        )
        self.assertRedirects(create_response, reverse("emotion_list"))
        created = Emotion.objects.get(libelle="Panique")

        list_response = self.client.get(reverse("emotion_list"), {"base": self.base.pk})
        self.assertEqual(list_response.status_code, 200)
        self.assertIn(created, list(list_response.context["emotions"]))

        update_response = self.client.post(
            reverse("emotion_edit", args=[created.pk]),
            data={"base": self.base.pk, "libelle": "Panique MAJ", "actif": "on"},
        )
        self.assertRedirects(update_response, reverse("emotion_list"))
        created.refresh_from_db()
        self.assertEqual(created.libelle, "Panique MAJ")

        delete_response = self.client.post(reverse("emotion_delete", args=[created.pk]))
        self.assertRedirects(delete_response, reverse("emotion_list"))
        self.assertFalse(Emotion.objects.filter(pk=created.pk).exists())


class EmotionsManagementCommandsTests(TestCase):
    def test_seed_emotions_populates_referential_and_is_idempotent(self):
        call_command("seed_emotions")
        base_count = EmotionBase.objects.count()
        emo_count = Emotion.objects.count()

        self.assertGreater(base_count, 0)
        self.assertGreater(emo_count, 0)

        call_command("seed_emotions")
        self.assertEqual(EmotionBase.objects.count(), base_count)
        self.assertEqual(Emotion.objects.count(), emo_count)

    def test_seed_emotions_reset_rebuilds_after_existing_data(self):
        base = EmotionBase.objects.create(libelle="Temp", actif=True)
        Emotion.objects.create(base=base, libelle="TempE", actif=True)

        call_command("seed_emotions", "--reset")

        self.assertFalse(EmotionBase.objects.filter(libelle="Temp").exists())
        self.assertGreater(EmotionBase.objects.count(), 0)

    def test_seed_legal_pages_creates_expected_pages(self):
        call_command("seed_legal_pages")

        self.assertTrue(PageInformation.objects.filter(slug="mentions-legales", statut="publie").exists())
        self.assertTrue(
            PageInformation.objects.filter(slug="donnees-personnelles", statut="publie").exists()
        )

    def test_seed_legal_pages_reset_clears_existing_pages_then_recreates(self):
        PageInformation.objects.create(
            titre="Custom",
            slug="custom-page",
            contenu="x",
            statut="publie",
            date_publication=timezone.now(),
        )

        call_command("seed_legal_pages", "--reset")

        self.assertFalse(PageInformation.objects.filter(slug="custom-page").exists())
        self.assertTrue(PageInformation.objects.filter(slug="mentions-legales").exists())
        self.assertTrue(PageInformation.objects.filter(slug="donnees-personnelles").exists())
