from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .forms import TrackerItemForm
from .models import Emotion, EmotionBase, TrackerItem
from .views import _period_start

User = get_user_model()


class TrackerItemFormTests(TestCase):
    def setUp(self):
        self.base_active = EmotionBase.objects.create(libelle="Joie", actif=True)
        self.base_inactive = EmotionBase.objects.create(libelle="Peur", actif=False)

        self.emotion_active = Emotion.objects.create(base=self.base_active, libelle="Gratitude", actif=True)
        Emotion.objects.create(base=self.base_active, libelle="Rage", actif=False)
        Emotion.objects.create(base=self.base_inactive, libelle="Anxiete", actif=True)

    def test_tracker_form_exposes_only_active_emotions_on_active_base(self):
        form = TrackerItemForm()

        self.assertQuerySetEqual(
            form.fields["emotion"].queryset,
            [self.emotion_active],
            ordered=True,
        )

    def test_tracker_form_sets_intensity_widget_bounds(self):
        form = TrackerItemForm()
        attrs = form.fields["intensite"].widget.attrs

        self.assertEqual(attrs["min"], 0)
        self.assertEqual(attrs["max"], 10)
        self.assertEqual(attrs["step"], 1)

    def test_tracker_item_accepts_intensity_between_0_and_10(self):
        user = User.objects.create_user(username="alice", password="pass1234")

        valid_low = TrackerItem(user=user, emotion=self.emotion_active, intensite=0)
        valid_high = TrackerItem(user=user, emotion=self.emotion_active, intensite=10)
        invalid_high = TrackerItem(user=user, emotion=self.emotion_active, intensite=11)

        valid_low.full_clean()
        valid_high.full_clean()

        with self.assertRaises(ValidationError):
            invalid_high.full_clean()


class PeriodStartTests(TestCase):
    def test_legacy_period_aliases_are_supported(self):
        self.assertEqual(_period_start("7d")[0], "week")
        self.assertEqual(_period_start("30d")[0], "month")
        self.assertEqual(_period_start("90d")[0], "quarter")
        self.assertEqual(_period_start("365d")[0], "year")

    def test_unknown_period_falls_back_to_month(self):
        period, start = _period_start("unknown")

        self.assertEqual(period, "month")
        self.assertIsNotNone(start.tzinfo)

    def test_none_and_empty_period_fall_back_to_month(self):
        self.assertEqual(_period_start(None)[0], "month")
        self.assertEqual(_period_start("")[0], "month")


class TrackerViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user1", password="pass1234")
        self.other_user = User.objects.create_user(username="user2", password="pass1234")

        self.base = EmotionBase.objects.create(libelle="Joie", actif=True)
        self.emotion = Emotion.objects.create(base=self.base, libelle="Gratitude", actif=True)
        self.inactive_emotion = Emotion.objects.create(base=self.base, libelle="Inactive", actif=False)

    def test_tracker_views_require_authentication(self):
        item = TrackerItem.objects.create(user=self.user, emotion=self.emotion, intensite=5)
        urls = [
            reverse("tracker_list"),
            reverse("tracker_add"),
            reverse("tracker_report"),
            reverse("tracker_edit", args=[item.pk]),
            reverse("tracker_delete", args=[item.pk]),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(f"{reverse('login')}?next="))

    def test_tracker_create_assigns_logged_user(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("tracker_add"),
            {"emotion": self.emotion.pk, "intensite": 7, "commentaire": "Bonne journee"},
        )

        self.assertRedirects(response, reverse("tracker_list"))
        self.assertEqual(TrackerItem.objects.count(), 1)

        item = TrackerItem.objects.get()
        self.assertEqual(item.user, self.user)
        self.assertEqual(item.emotion, self.emotion)
        self.assertEqual(item.intensite, 7)

    def test_tracker_create_get_renders_form(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("tracker_add"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/tracker_form.html")
        self.assertEqual(response.context["mode"], "create")
        self.assertIn("form", response.context)

    def test_tracker_create_invalid_post_returns_form_errors(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("tracker_add"),
            {"emotion": self.emotion.pk, "intensite": 11, "commentaire": "invalid"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/tracker_form.html")
        self.assertIn("intensite", response.context["form"].errors)
        self.assertEqual(TrackerItem.objects.count(), 0)

    def test_tracker_create_rejects_inactive_emotion(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("tracker_add"),
            {"emotion": self.inactive_emotion.pk, "intensite": 3, "commentaire": "test"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(TrackerItem.objects.count(), 0)
        self.assertIn("valid choice", response.context["form"].errors["emotion"][0])

    def test_tracker_update_only_allows_owner(self):
        own_item = TrackerItem.objects.create(user=self.user, emotion=self.emotion, intensite=3)
        other_item = TrackerItem.objects.create(user=self.other_user, emotion=self.emotion, intensite=4)

        self.client.force_login(self.user)

        denied = self.client.post(
            reverse("tracker_edit", args=[other_item.pk]),
            {"emotion": self.emotion.pk, "intensite": 8, "commentaire": "forbidden"},
        )
        self.assertEqual(denied.status_code, 404)

        allowed = self.client.post(
            reverse("tracker_edit", args=[own_item.pk]),
            {"emotion": self.emotion.pk, "intensite": 9, "commentaire": "updated"},
        )
        self.assertRedirects(allowed, reverse("tracker_list"))

        own_item.refresh_from_db()
        self.assertEqual(own_item.intensite, 9)
        self.assertEqual(own_item.commentaire, "updated")

    def test_tracker_update_get_renders_form_for_owner(self):
        own_item = TrackerItem.objects.create(user=self.user, emotion=self.emotion, intensite=3)
        self.client.force_login(self.user)

        response = self.client.get(reverse("tracker_edit", args=[own_item.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/tracker_form.html")
        self.assertEqual(response.context["mode"], "edit")
        self.assertEqual(response.context["item"], own_item)

    def test_tracker_update_invalid_post_returns_form_errors(self):
        own_item = TrackerItem.objects.create(
            user=self.user,
            emotion=self.emotion,
            intensite=3,
            commentaire="before",
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("tracker_edit", args=[own_item.pk]),
            {"emotion": self.emotion.pk, "intensite": 99, "commentaire": "after"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/tracker_form.html")
        self.assertIn("intensite", response.context["form"].errors)
        own_item.refresh_from_db()
        self.assertEqual(own_item.intensite, 3)
        self.assertEqual(own_item.commentaire, "before")

    def test_tracker_delete_only_allows_owner(self):
        own_item = TrackerItem.objects.create(user=self.user, emotion=self.emotion, intensite=3)
        other_item = TrackerItem.objects.create(user=self.other_user, emotion=self.emotion, intensite=4)

        self.client.force_login(self.user)

        denied = self.client.post(reverse("tracker_delete", args=[other_item.pk]))
        self.assertEqual(denied.status_code, 404)

        allowed = self.client.post(reverse("tracker_delete", args=[own_item.pk]))
        self.assertRedirects(allowed, reverse("tracker_list"))
        self.assertFalse(TrackerItem.objects.filter(pk=own_item.pk).exists())

    def test_tracker_delete_get_renders_confirmation(self):
        own_item = TrackerItem.objects.create(user=self.user, emotion=self.emotion, intensite=3)
        self.client.force_login(self.user)

        response = self.client.get(reverse("tracker_delete", args=[own_item.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/tracker_delete.html")
        self.assertEqual(response.context["item"], own_item)

    def test_tracker_list_filters_by_period_and_user(self):
        self.client.force_login(self.user)

        in_period = TrackerItem.objects.create(user=self.user, emotion=self.emotion, intensite=6)
        out_of_period = TrackerItem.objects.create(user=self.user, emotion=self.emotion, intensite=2)
        other_user_item = TrackerItem.objects.create(user=self.other_user, emotion=self.emotion, intensite=5)

        _, month_start = _period_start("month")
        TrackerItem.objects.filter(pk=out_of_period.pk).update(date_saisie=month_start - timedelta(minutes=1))

        response = self.client.get(reverse("tracker_list"), {"period": "month"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["period"], "month")

        items = list(response.context["items"])
        self.assertIn(in_period, items)
        self.assertNotIn(out_of_period, items)
        self.assertNotIn(other_user_item, items)

    def test_tracker_list_accepts_legacy_period_alias(self):
        self.client.force_login(self.user)

        in_week = TrackerItem.objects.create(user=self.user, emotion=self.emotion, intensite=6)
        out_week = TrackerItem.objects.create(user=self.user, emotion=self.emotion, intensite=2)

        _, week_start = _period_start("week")
        TrackerItem.objects.filter(pk=out_week.pk).update(date_saisie=week_start - timedelta(minutes=1))

        response = self.client.get(reverse("tracker_list"), {"period": "7d"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["period"], "week")
        items = list(response.context["items"])
        self.assertIn(in_week, items)
        self.assertNotIn(out_week, items)

    def test_tracker_list_unknown_period_falls_back_to_month(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("tracker_list"), {"period": "something-else"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["period"], "month")

    def test_tracker_report_aggregates_by_base_and_emotion(self):
        self.client.force_login(self.user)

        emotion_two = Emotion.objects.create(base=self.base, libelle="Fierte", actif=True)

        TrackerItem.objects.create(user=self.user, emotion=self.emotion, intensite=4)
        TrackerItem.objects.create(user=self.user, emotion=self.emotion, intensite=6)
        TrackerItem.objects.create(user=self.user, emotion=emotion_two, intensite=None)
        TrackerItem.objects.create(user=self.other_user, emotion=self.emotion, intensite=10)

        old_item = TrackerItem.objects.create(user=self.user, emotion=self.emotion, intensite=8)
        _, month_start = _period_start("month")
        TrackerItem.objects.filter(pk=old_item.pk).update(date_saisie=month_start - timedelta(minutes=1))

        response = self.client.get(reverse("tracker_report"), {"period": "month"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["period"], "month")

        by_base = list(response.context["by_base"])
        base_row = next(row for row in by_base if row["emotion__base__libelle"] == "Joie")
        self.assertEqual(base_row["nb"], 3)
        self.assertAlmostEqual(base_row["avg_int"], 5.0)

        by_emotion = {
            row["emotion__libelle"]: row["nb"]
            for row in response.context["by_emotion"]
        }
        self.assertEqual(by_emotion["Gratitude"], 2)
        self.assertEqual(by_emotion["Fierte"], 1)

    def test_tracker_report_accepts_legacy_period_alias(self):
        self.client.force_login(self.user)

        TrackerItem.objects.create(user=self.user, emotion=self.emotion, intensite=4)

        response = self.client.get(reverse("tracker_report"), {"period": "90d"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["period"], "quarter")

    def test_tracker_report_unknown_period_falls_back_to_month(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("tracker_report"), {"period": "not-a-period"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["period"], "month")

    def test_tracker_report_empty_period_returns_empty_groups(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("tracker_report"), {"period": "month"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["by_base"]), [])
        self.assertEqual(list(response.context["by_emotion"]), [])


class EmotionsAdminViewsTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username="admin", password="pass1234", is_staff=True)
        self.regular_user = User.objects.create_user(username="regular", password="pass1234")

        self.base_one = EmotionBase.objects.create(libelle="Joie", actif=True)
        self.base_two = EmotionBase.objects.create(libelle="Peur", actif=True)
        self.emotion_one = Emotion.objects.create(base=self.base_one, libelle="Gratitude", actif=True)
        self.emotion_two = Emotion.objects.create(base=self.base_two, libelle="Anxiete", actif=True)

    def test_admin_views_redirect_when_not_admin(self):
        url = reverse("base_list")

        anonymous_response = self.client.get(url)
        self.assertEqual(anonymous_response.status_code, 302)
        self.assertTrue(anonymous_response.url.startswith(f"{reverse('login')}?next="))

        self.client.force_login(self.regular_user)
        regular_response = self.client.get(url)
        self.assertEqual(regular_response.status_code, 302)
        self.assertTrue(regular_response.url.startswith(f"{reverse('login')}?next="))

    def test_admin_can_crud_emotion_base(self):
        self.client.force_login(self.admin_user)

        create_response = self.client.post(reverse("base_add"), {"libelle": "Colere", "actif": "on"})
        self.assertRedirects(create_response, reverse("base_list"))

        base = EmotionBase.objects.get(libelle="Colere")

        update_response = self.client.post(
            reverse("base_edit", args=[base.pk]),
            {"libelle": "Colere modifiee"},
        )
        self.assertRedirects(update_response, reverse("base_list"))

        base.refresh_from_db()
        self.assertEqual(base.libelle, "Colere modifiee")
        self.assertFalse(base.actif)

        delete_response = self.client.post(reverse("base_delete", args=[base.pk]))
        self.assertRedirects(delete_response, reverse("base_list"))
        self.assertFalse(EmotionBase.objects.filter(pk=base.pk).exists())

    def test_admin_base_list_get_renders_page(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("base_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/admin/base_list.html")
        bases = list(response.context["bases"])
        self.assertIn(self.base_one, bases)
        self.assertIn(self.base_two, bases)

    def test_admin_base_create_get_renders_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("base_add"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/admin/base_form.html")
        self.assertEqual(response.context["mode"], "create")
        self.assertIn("form", response.context)

    def test_admin_base_create_invalid_post_returns_form_errors(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(reverse("base_add"), {"libelle": "", "actif": "on"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/admin/base_form.html")
        self.assertIn("libelle", response.context["form"].errors)

    def test_admin_base_update_get_renders_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("base_edit", args=[self.base_one.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/admin/base_form.html")
        self.assertEqual(response.context["mode"], "edit")
        self.assertEqual(response.context["base"], self.base_one)

    def test_admin_base_update_invalid_post_keeps_existing_value(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(reverse("base_edit", args=[self.base_one.pk]), {"libelle": ""})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/admin/base_form.html")
        self.assertIn("libelle", response.context["form"].errors)
        self.base_one.refresh_from_db()
        self.assertEqual(self.base_one.libelle, "Joie")

    def test_admin_base_delete_get_renders_confirmation(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("base_delete", args=[self.base_one.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/admin/base_delete.html")
        self.assertEqual(response.context["base"], self.base_one)

    def test_admin_can_crud_emotion(self):
        self.client.force_login(self.admin_user)

        create_response = self.client.post(
            reverse("emotion_add"),
            {"base": self.base_one.pk, "libelle": "Satisfaction", "actif": "on"},
        )
        self.assertRedirects(create_response, reverse("emotion_list"))

        emotion = Emotion.objects.get(base=self.base_one, libelle="Satisfaction")

        update_response = self.client.post(
            reverse("emotion_edit", args=[emotion.pk]),
            {"base": self.base_two.pk, "libelle": "Soulagement"},
        )
        self.assertRedirects(update_response, reverse("emotion_list"))

        emotion.refresh_from_db()
        self.assertEqual(emotion.base, self.base_two)
        self.assertEqual(emotion.libelle, "Soulagement")
        self.assertFalse(emotion.actif)

        delete_response = self.client.post(reverse("emotion_delete", args=[emotion.pk]))
        self.assertRedirects(delete_response, reverse("emotion_list"))
        self.assertFalse(Emotion.objects.filter(pk=emotion.pk).exists())

    def test_admin_emotion_create_get_renders_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("emotion_add"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/admin/emotion_form.html")
        self.assertEqual(response.context["mode"], "create")
        self.assertIn("form", response.context)

    def test_admin_emotion_create_invalid_post_returns_form_errors(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(reverse("emotion_add"), {"base": self.base_one.pk, "libelle": ""})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/admin/emotion_form.html")
        self.assertIn("libelle", response.context["form"].errors)

    def test_admin_emotion_update_get_renders_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("emotion_edit", args=[self.emotion_one.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/admin/emotion_form.html")
        self.assertEqual(response.context["mode"], "edit")
        self.assertEqual(response.context["emo"], self.emotion_one)

    def test_admin_emotion_update_invalid_post_keeps_existing_value(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("emotion_edit", args=[self.emotion_one.pk]),
            {"base": self.base_one.pk, "libelle": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/admin/emotion_form.html")
        self.assertIn("libelle", response.context["form"].errors)
        self.emotion_one.refresh_from_db()
        self.assertEqual(self.emotion_one.libelle, "Gratitude")

    def test_admin_emotion_delete_get_renders_confirmation(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("emotion_delete", args=[self.emotion_one.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emotions/admin/emotion_delete.html")
        self.assertEqual(response.context["emo"], self.emotion_one)

    def test_admin_emotion_list_supports_base_filter(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("emotion_list"), {"base": self.base_one.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["base_id"], str(self.base_one.pk))

        emotions = list(response.context["emotions"])
        self.assertIn(self.emotion_one, emotions)
        self.assertNotIn(self.emotion_two, emotions)

    def test_admin_emotion_list_without_filter_returns_all(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("emotion_list"))

        self.assertEqual(response.status_code, 200)
        emotions = list(response.context["emotions"])
        self.assertIn(self.emotion_one, emotions)
        self.assertIn(self.emotion_two, emotions)
        self.assertIn("bases", response.context)
