from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import PageInformationForm
from .models import PageInformation
from .views import _published_articles

User = get_user_model()


class InfosModelAndFormTests(TestCase):
    def test_page_information_str_returns_title(self):
        page = PageInformation.objects.create(
            titre="Mon article",
            slug="mon-article",
            contenu="Contenu",
            statut="publie",
            date_publication=timezone.now(),
        )

        self.assertEqual(str(page), "Mon article")

    def test_page_information_form_autogenerates_slug_from_title(self):
        form = PageInformationForm()
        form.cleaned_data = {"titre": "Gestion du stress", "slug": ""}

        self.assertEqual(form.clean_slug(), "gestion-du-stress")

    def test_page_information_form_keeps_given_slug(self):
        form = PageInformationForm(
            data={
                "titre": "Gestion du stress",
                "slug": "slug-perso",
                "contenu": "Texte",
                "statut": "publie",
                "date_publication": timezone.now(),
            }
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["slug"], "slug-perso")

    def test_published_articles_returns_only_published_non_legal(self):
        now = timezone.now()
        public_page = PageInformation.objects.create(
            titre="A",
            slug="a",
            contenu="x",
            statut="publie",
            date_publication=now,
        )
        PageInformation.objects.create(
            titre="Brouillon",
            slug="brouillon",
            contenu="x",
            statut="brouillon",
            date_publication=now,
        )
        PageInformation.objects.create(
            titre="Archive",
            slug="archive",
            contenu="x",
            statut="archive",
            date_publication=now,
        )
        PageInformation.objects.create(
            titre="Mentions",
            slug="mentions-legales",
            contenu="x",
            statut="publie",
            date_publication=now,
        )

        results = list(_published_articles())

        self.assertEqual(results, [public_page])

    def test_published_articles_orders_by_publication_then_update_date(self):
        now = timezone.now()

        old_page = PageInformation.objects.create(
            titre="Old",
            slug="old",
            contenu="x",
            statut="publie",
            date_publication=now - timedelta(days=2),
        )
        same_pub_one = PageInformation.objects.create(
            titre="Same One",
            slug="same-one",
            contenu="x",
            statut="publie",
            date_publication=now - timedelta(days=1),
        )
        same_pub_two = PageInformation.objects.create(
            titre="Same Two",
            slug="same-two",
            contenu="x",
            statut="publie",
            date_publication=now - timedelta(days=1),
        )

        # Force date_mise_a_jour to differentiate same publication date rows.
        PageInformation.objects.filter(pk=same_pub_one.pk).update(date_mise_a_jour=now - timedelta(hours=3))
        PageInformation.objects.filter(pk=same_pub_two.pk).update(date_mise_a_jour=now - timedelta(hours=1))
        PageInformation.objects.filter(pk=old_page.pk).update(date_mise_a_jour=now - timedelta(hours=2))

        ordered = list(_published_articles())

        self.assertEqual(ordered[0], same_pub_two)
        self.assertEqual(ordered[1], same_pub_one)
        self.assertEqual(ordered[2], old_page)

    def test_published_articles_limit_parameter(self):
        now = timezone.now()
        for idx in range(6):
            PageInformation.objects.create(
                titre=f"Article {idx}",
                slug=f"article-{idx}",
                contenu="x",
                statut="publie",
                date_publication=now - timedelta(days=idx),
            )

        results = list(_published_articles(limit=4))

        self.assertEqual(len(results), 4)


class InfosPublicViewsTests(TestCase):
    def setUp(self):
        now = timezone.now()

        self.public_page = PageInformation.objects.create(
            titre="Article public",
            slug="article-public",
            contenu="contenu public",
            statut="publie",
            date_publication=now - timedelta(days=1),
        )
        self.second_public_page = PageInformation.objects.create(
            titre="Article public 2",
            slug="article-public-2",
            contenu="contenu public 2",
            statut="publie",
            date_publication=now - timedelta(days=2),
        )
        self.draft_page = PageInformation.objects.create(
            titre="Brouillon",
            slug="brouillon",
            contenu="contenu brouillon",
            statut="brouillon",
            date_publication=now,
        )
        self.archived_page = PageInformation.objects.create(
            titre="Archive",
            slug="archive",
            contenu="contenu archive",
            statut="archive",
            date_publication=now,
        )
        self.legal_page = PageInformation.objects.create(
            titre="Mentions",
            slug="mentions-legales",
            contenu="mentions",
            statut="publie",
            date_publication=now,
        )

    def test_home_view_renders_with_tracker_and_limited_articles(self):
        # Add extra published rows so home must limit to 4.
        now = timezone.now()
        for idx in range(5):
            PageInformation.objects.create(
                titre=f"Extra {idx}",
                slug=f"extra-{idx}",
                contenu="x",
                statut="publie",
                date_publication=now - timedelta(minutes=idx),
            )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "infos/home.html")
        self.assertTrue(response.context["show_tracker"])
        self.assertEqual(response.context["page_heading"], "Bienvenue sur CESIZen")
        self.assertEqual(len(list(response.context["latest_articles"])), 4)

        slugs = {page.slug for page in response.context["latest_articles"]}
        self.assertNotIn("mentions-legales", slugs)
        self.assertNotIn("brouillon", slugs)
        self.assertNotIn("archive", slugs)

    def test_articles_view_renders_all_published_non_legal(self):
        response = self.client.get(reverse("articles"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "infos/home.html")
        self.assertFalse(response.context["show_tracker"])
        self.assertEqual(response.context["page_heading"], "Articles")

        articles = list(response.context["latest_articles"])
        self.assertIn(self.public_page, articles)
        self.assertIn(self.second_public_page, articles)
        self.assertNotIn(self.draft_page, articles)
        self.assertNotIn(self.archived_page, articles)
        self.assertNotIn(self.legal_page, articles)

    def test_page_detail_returns_200_for_published_page(self):
        response = self.client.get(reverse("page_detail", args=[self.public_page.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "infos/page_detail.html")
        self.assertEqual(response.context["page"], self.public_page)

    def test_page_detail_returns_404_for_draft_page(self):
        response = self.client.get(reverse("page_detail", args=[self.draft_page.slug]))

        self.assertEqual(response.status_code, 404)

    def test_page_detail_returns_404_for_archived_page(self):
        response = self.client.get(reverse("page_detail", args=[self.archived_page.slug]))

        self.assertEqual(response.status_code, 404)

    def test_page_detail_returns_404_for_unknown_slug(self):
        response = self.client.get(reverse("page_detail", args=["inexistant"]))

        self.assertEqual(response.status_code, 404)


class InfosAdminViewsTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass1234",
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="pass1234",
        )
        self.group_admin_user = User.objects.create_user(
            username="group-admin",
            email="group-admin@example.com",
            password="pass1234",
        )
        admin_group = Group.objects.create(name="ADMIN")
        self.group_admin_user.groups.add(admin_group)

        self.page = PageInformation.objects.create(
            titre="Page cible",
            slug="page-cible",
            contenu="contenu",
            statut="brouillon",
        )

    def test_admin_pages_redirect_for_anonymous_and_non_admin(self):
        anonymous = self.client.get(reverse("page_admin_list"))
        self.assertEqual(anonymous.status_code, 302)
        self.assertTrue(anonymous.url.startswith(f"{reverse('login')}?next="))

        self.client.force_login(self.regular_user)
        regular = self.client.get(reverse("page_admin_list"))
        self.assertEqual(regular.status_code, 302)
        self.assertTrue(regular.url.startswith(f"{reverse('login')}?next="))

    def test_admin_pages_access_for_staff_and_group_admin(self):
        self.client.force_login(self.admin_user)
        staff_response = self.client.get(reverse("page_admin_list"))
        self.assertEqual(staff_response.status_code, 200)
        self.client.logout()

        self.client.force_login(self.group_admin_user)
        group_response = self.client.get(reverse("page_admin_list"))
        self.assertEqual(group_response.status_code, 200)

    def test_page_list_get_renders_page_list(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("page_admin_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "infos/admin/page_list.html")
        self.assertIn(self.page, list(response.context["pages"]))

    def test_page_create_get_renders_form_with_default_statut(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("page_admin_add"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "infos/admin/page_form.html")
        self.assertEqual(response.context["mode"], "create")
        self.assertEqual(response.context["form"].initial["statut"], "publie")

    def test_page_create_post_valid_published_sets_publication_date(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("page_admin_add"),
            data={
                "titre": "Nouvelle page",
                "slug": "nouvelle-page",
                "contenu": "Texte",
                "statut": "publie",
                "date_publication": "",
            },
        )

        self.assertRedirects(response, reverse("page_admin_list"))
        created = PageInformation.objects.get(slug="nouvelle-page")
        self.assertEqual(created.statut, "publie")
        self.assertIsNotNone(created.date_publication)

    def test_page_create_post_valid_brouillon_keeps_publication_date_empty(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("page_admin_add"),
            data={
                "titre": "Brouillon neuf",
                "slug": "brouillon-neuf",
                "contenu": "Texte",
                "statut": "brouillon",
                "date_publication": "",
            },
        )

        self.assertRedirects(response, reverse("page_admin_list"))
        created = PageInformation.objects.get(slug="brouillon-neuf")
        self.assertIsNone(created.date_publication)

    def test_page_create_post_invalid_renders_form_errors(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("page_admin_add"),
            data={
                "titre": "",
                "slug": "",
                "contenu": "",
                "statut": "publie",
                "date_publication": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "infos/admin/page_form.html")
        self.assertEqual(response.context["mode"], "create")
        self.assertIn("titre", response.context["form"].errors)

    def test_page_update_get_renders_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("page_admin_edit", args=[self.page.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "infos/admin/page_form.html")
        self.assertEqual(response.context["mode"], "edit")
        self.assertEqual(response.context["page"], self.page)

    def test_page_update_post_valid_sets_publication_date_if_needed(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("page_admin_edit", args=[self.page.pk]),
            data={
                "titre": "Page cible",
                "slug": "page-cible",
                "contenu": "maj",
                "statut": "publie",
                "date_publication": "",
            },
        )

        self.assertRedirects(response, reverse("page_admin_list"))
        self.page.refresh_from_db()
        self.assertEqual(self.page.statut, "publie")
        self.assertEqual(self.page.contenu, "maj")
        self.assertIsNotNone(self.page.date_publication)

    def test_page_update_post_keeps_existing_publication_date(self):
        self.client.force_login(self.admin_user)

        existing_pub = timezone.now() - timedelta(days=3)
        PageInformation.objects.filter(pk=self.page.pk).update(
            statut="publie",
            date_publication=existing_pub,
        )

        response = self.client.post(
            reverse("page_admin_edit", args=[self.page.pk]),
            data={
                "titre": "Page cible",
                "slug": "page-cible",
                "contenu": "maj-2",
                "statut": "publie",
                "date_publication": existing_pub.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

        self.assertRedirects(response, reverse("page_admin_list"))
        self.page.refresh_from_db()
        self.assertEqual(self.page.date_publication, existing_pub.replace(microsecond=0, tzinfo=existing_pub.tzinfo))

    def test_page_update_post_invalid_renders_errors_and_keeps_data(self):
        self.client.force_login(self.admin_user)
        original_titre = self.page.titre

        response = self.client.post(
            reverse("page_admin_edit", args=[self.page.pk]),
            data={
                "titre": "",
                "slug": "page-cible",
                "contenu": "maj",
                "statut": "publie",
                "date_publication": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "infos/admin/page_form.html")
        self.assertIn("titre", response.context["form"].errors)
        self.page.refresh_from_db()
        self.assertEqual(self.page.titre, original_titre)

    def test_page_update_unknown_pk_returns_404(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("page_admin_edit", args=[999999]))

        self.assertEqual(response.status_code, 404)

    def test_page_delete_get_renders_confirmation(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("page_admin_delete", args=[self.page.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "infos/admin/page_delete.html")
        self.assertEqual(response.context["page"], self.page)

    def test_page_delete_post_deletes_page(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(reverse("page_admin_delete", args=[self.page.pk]))

        self.assertRedirects(response, reverse("page_admin_list"))
        self.assertFalse(PageInformation.objects.filter(pk=self.page.pk).exists())

    def test_page_delete_unknown_pk_returns_404(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("page_admin_delete", args=[999999]))

        self.assertEqual(response.status_code, 404)
