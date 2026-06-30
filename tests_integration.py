"""
Integration tests for CEZIZen.

Tests cross-app workflows and multi-step user journeys that span multiple apps.

Run with:  python manage.py test tests_integration
"""
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User
from emotions.models import EmotionBase, Emotion, TrackerItem
from infos.models import PageInformation


# ---------------------------------------------------------------------------
# Workflow: signup → login → tracker entry → list → report
# ---------------------------------------------------------------------------

class SignupToTrackerWorkflowTest(TestCase):
    """Full new-user journey: signup → login → add tracker entry → view it."""

    def setUp(self):
        base = EmotionBase.objects.create(libelle="Joie")
        self.emotion = Emotion.objects.create(base=base, libelle="Enthousiasme")

    def test_signup_then_track_emotion(self):
        c = Client()

        # 1. Signup
        resp = c.post(reverse("signup"), {
            "username": "newuser",
            "email": "new@test.com",
            "password1": "Str0ngPass!99",
            "password2": "Str0ngPass!99",
            "rgpd_accepte": True,
        })
        self.assertEqual(resp.status_code, 302)

        user = User.objects.get(username="newuser")
        self.assertTrue(user.rgpd_accepte)
        self.assertIsNotNone(user.rgpd_date_acceptation)

        # 2. Login
        c.login(username="newuser", password="Str0ngPass!99")

        # 3. Create a tracker entry
        resp = c.post(reverse("tracker_add"), {
            "emotion": self.emotion.pk,
            "intensite": 7,
            "commentaire": "Premier suivi",
        })
        self.assertEqual(resp.status_code, 302)

        # 4. Entry exists and belongs to user
        item = TrackerItem.objects.get(user=user)
        self.assertEqual(item.emotion, self.emotion)
        self.assertEqual(item.intensite, 7)

        # 5. Tracker list includes the entry
        resp = c.get(reverse("tracker_list") + "?period=all")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(item, list(resp.context["items"]))

        # 6. Report accessible without error
        resp = c.get(reverse("tracker_report") + "?period=all")
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# Cross-app: admin creates emotion → regular user sees it in tracker form
# ---------------------------------------------------------------------------

class AdminEmotionVisibleInTrackerTest(TestCase):
    """Admin creates an emotion → it immediately appears in the tracker form."""

    def setUp(self):
        self.admin = User.objects.create_user("admin", password="admin123!", is_staff=True)
        self.user = User.objects.create_user("user", password="user123!")

    def test_new_emotion_appears_in_tracker_form(self):
        admin_c = Client()
        admin_c.login(username="admin", password="admin123!")

        # Admin creates an emotion base
        resp = admin_c.post(reverse("base_add"), {"libelle": "Sérénité", "actif": True})
        self.assertEqual(resp.status_code, 302)
        base = EmotionBase.objects.get(libelle="Sérénité")

        # Admin creates an emotion under that base
        resp = admin_c.post(reverse("emotion_add"), {
            "base": base.pk, "libelle": "Calme", "actif": True,
        })
        self.assertEqual(resp.status_code, 302)
        emotion = Emotion.objects.get(libelle="Calme")

        # Regular user opens the tracker form
        user_c = Client()
        user_c.login(username="user", password="user123!")
        resp = user_c.get(reverse("tracker_add"))
        self.assertEqual(resp.status_code, 200)

        # The new emotion is in the choices
        form_qs = list(resp.context["form"].fields["emotion"].queryset)
        self.assertIn(emotion, form_qs)


# ---------------------------------------------------------------------------
# Cross-app: admin publishes page → visible publicly
# ---------------------------------------------------------------------------

class AdminPublishPageTest(TestCase):
    """Admin publishes a page → it appears on the home page and via its slug."""

    def setUp(self):
        self.admin = User.objects.create_user("admin", password="admin123!", is_staff=True)

    def test_published_page_on_home_and_detail(self):
        c = Client()
        c.login(username="admin", password="admin123!")

        # Admin creates a published page (no date → auto-set)
        resp = c.post(reverse("page_admin_add"), {
            "titre": "Article intégration",
            "slug": "article-integration",
            "contenu": "Contenu de test.",
            "statut": "publie",
            "date_publication": "",
        })
        self.assertEqual(resp.status_code, 302)

        page = PageInformation.objects.get(slug="article-integration")
        self.assertEqual(page.statut, "publie")
        self.assertIsNotNone(page.date_publication)   # auto-set by view

        # Anonymous user sees it on the home page
        anon = Client()
        resp = anon.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        slugs = [p.slug for p in resp.context["latest_articles"]]
        self.assertIn("article-integration", slugs)

        # Page detail is reachable
        resp = anon.get(reverse("page_detail", kwargs={"slug": "article-integration"}))
        self.assertEqual(resp.status_code, 200)

    def test_draft_page_returns_404_on_detail(self):
        PageInformation.objects.create(
            titre="Brouillon", slug="brouillon-test",
            contenu="Non publié.", statut="brouillon",
        )
        resp = Client().get(reverse("page_detail", kwargs={"slug": "brouillon-test"}))
        self.assertEqual(resp.status_code, 404)


# ---------------------------------------------------------------------------
# Data isolation: two users cannot access each other's tracker entries
# ---------------------------------------------------------------------------

class TrackerUserIsolationTest(TestCase):
    """Two users' tracker entries are fully isolated."""

    def setUp(self):
        base = EmotionBase.objects.create(libelle="Peur")
        self.emotion = Emotion.objects.create(base=base, libelle="Anxiété")
        self.u1 = User.objects.create_user("user1", password="pass1234!")
        self.u2 = User.objects.create_user("user2", password="pass1234!")

    def test_cannot_edit_or_delete_another_users_entry(self):
        item = TrackerItem.objects.create(user=self.u1, emotion=self.emotion, intensite=5)

        c2 = Client()
        c2.login(username="user2", password="pass1234!")

        # Edit → 404 (ownership enforced by get_object_or_404)
        self.assertEqual(
            c2.get(reverse("tracker_edit", kwargs={"pk": item.pk})).status_code, 404
        )
        # Delete → 404
        self.assertEqual(
            c2.post(reverse("tracker_delete", kwargs={"pk": item.pk})).status_code, 404
        )

    def test_list_shows_only_own_entries(self):
        item1 = TrackerItem.objects.create(user=self.u1, emotion=self.emotion, intensite=4)
        item2 = TrackerItem.objects.create(user=self.u2, emotion=self.emotion, intensite=6)

        c1 = Client()
        c1.login(username="user1", password="pass1234!")
        resp = c1.get(reverse("tracker_list") + "?period=all")

        items = list(resp.context["items"])
        self.assertIn(item1, items)
        self.assertNotIn(item2, items)


# ---------------------------------------------------------------------------
# DB integrity: PROTECT prevents deleting referenced emotions
# ---------------------------------------------------------------------------

class EmotionDeleteProtectionTest(TestCase):
    """Admin cannot delete an emotion that is referenced by a tracker item."""

    def setUp(self):
        self.admin = User.objects.create_user("admin", password="admin123!", is_staff=True)
        user = User.objects.create_user("user", password="user123!")
        base = EmotionBase.objects.create(libelle="Tristesse")
        self.emotion = Emotion.objects.create(base=base, libelle="Mélancolie")
        TrackerItem.objects.create(user=user, emotion=self.emotion, intensite=3)

    def test_emotion_not_deleted_when_referenced(self):
        c = Client()
        c.login(username="admin", password="admin123!")
        # The view raises ProtectedError (no try/except); disable re-raise so
        # we can assert the database state instead of catching the exception.
        c.raise_request_exception = False
        c.post(reverse("emotion_delete", kwargs={"pk": self.emotion.pk}))

        self.assertTrue(Emotion.objects.filter(pk=self.emotion.pk).exists())


# ---------------------------------------------------------------------------
# DB integrity: deleting a user cascades to tracker items
# ---------------------------------------------------------------------------

class UserDeletionCascadesTrackerTest(TestCase):
    """Deleting a user removes all their tracker items (CASCADE)."""

    def setUp(self):
        base = EmotionBase.objects.create(libelle="Joie")
        emotion = Emotion.objects.create(base=base, libelle="Bonheur")
        self.user = User.objects.create_user("todelete", password="pass1234!")
        TrackerItem.objects.create(user=self.user, emotion=emotion, intensite=8)
        TrackerItem.objects.create(user=self.user, emotion=emotion, intensite=6)

    def test_tracker_items_cascade_on_user_delete(self):
        user_pk = self.user.pk
        self.assertEqual(TrackerItem.objects.filter(user_id=user_pk).count(), 2)

        self.user.delete()

        self.assertEqual(TrackerItem.objects.filter(user_id=user_pk).count(), 0)


# ---------------------------------------------------------------------------
# Admin workflow: deactivate user → login no longer possible
# ---------------------------------------------------------------------------

class AdminDeactivatesUserTest(TestCase):
    """Admin deactivates a user account → the user can no longer log in."""

    def setUp(self):
        self.staff = User.objects.create_user("staff", password="staff123!", is_staff=True)
        self.target = User.objects.create_user(
            "target", email="target@test.com", password="target123!"
        )

    def test_deactivated_user_cannot_login(self):
        # Baseline: target can log in
        self.assertTrue(Client().login(username="target", password="target123!"))

        # Admin deactivates the account via the admin UI
        c = Client()
        c.login(username="staff", password="staff123!")
        resp = c.post(reverse("user_admin_edit", kwargs={"pk": self.target.pk}), {
            "username": "target",
            "email": "target@test.com",
            "is_active": False,
            "is_staff": False,
        })
        self.assertEqual(resp.status_code, 302)

        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)

        # Target can no longer log in
        self.assertFalse(Client().login(username="target", password="target123!"))


# ---------------------------------------------------------------------------
# Permission boundaries
# ---------------------------------------------------------------------------

class PermissionBoundariesTest(TestCase):
    """Unauthenticated users are redirected; regular users blocked from admin views."""

    def setUp(self):
        self.regular = User.objects.create_user("regular", password="pass1234!")

    def test_anonymous_redirected_from_login_required_views(self):
        c = Client()
        login_url = reverse("login")
        for url_name in ["tracker_list", "tracker_add", "tracker_report", "profile"]:
            resp = c.get(reverse(url_name))
            self.assertEqual(resp.status_code, 302, f"{url_name} should redirect")
            self.assertIn(login_url, resp["Location"])

    def test_regular_user_blocked_from_admin_views(self):
        c = Client()
        c.login(username="regular", password="pass1234!")
        for url_name in ["base_list", "emotion_list", "page_admin_list", "user_admin_list"]:
            resp = c.get(reverse(url_name))
            # user_passes_test redirects to login when the test fails
            self.assertEqual(resp.status_code, 302, f"{url_name} should block regular user")
