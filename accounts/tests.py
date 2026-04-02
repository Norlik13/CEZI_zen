from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.auth.tokens import default_token_generator
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .context_processors import admin_context
from .forms import SignUpForm
from .permissions import is_admin

User = get_user_model()


class AccountsPermissionsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_group = Group.objects.create(name="ADMIN")

        self.staff_user = User.objects.create_user(
            username="staff_user",
            password="pass1234",
            is_staff=True,
        )
        self.group_admin_user = User.objects.create_user(
            username="group_admin_user",
            password="pass1234",
        )
        self.group_admin_user.groups.add(self.admin_group)

        self.regular_user = User.objects.create_user(
            username="regular_user",
            password="pass1234",
        )

    def test_is_admin_returns_false_for_anonymous_user(self):
        self.assertFalse(is_admin(AnonymousUser()))

    def test_is_admin_returns_true_for_staff_user(self):
        self.assertTrue(is_admin(self.staff_user))

    def test_is_admin_returns_true_for_admin_group_user(self):
        self.assertTrue(is_admin(self.group_admin_user))

    def test_is_admin_returns_false_for_regular_user(self):
        self.assertFalse(is_admin(self.regular_user))

    def test_admin_context_exposes_is_admin_user_flag(self):
        request = self.factory.get("/")
        request.user = self.group_admin_user

        context = admin_context(request)

        self.assertEqual(context, {"is_admin_user": True})


class AccountsModelTests(TestCase):
    def test_accept_rgpd_sets_flag_and_acceptance_date(self):
        user = User.objects.create_user(username="alice", password="pass1234")

        user.accept_rgpd()
        user.refresh_from_db()

        self.assertTrue(user.rgpd_accepte)
        self.assertIsNotNone(user.rgpd_date_acceptation)


class SignUpFormTests(TestCase):
    def test_signup_form_requires_rgpd_checkbox(self):
        form = SignUpForm(
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("rgpd_accepte", form.errors)

    def test_signup_form_save_sets_email_and_rgpd_fields(self):
        form = SignUpForm(
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "rgpd_accepte": True,
            }
        )

        self.assertTrue(form.is_valid())
        user = form.save()

        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(user.rgpd_accepte)
        self.assertIsNotNone(user.rgpd_date_acceptation)

    def test_signup_form_save_with_commit_false_does_not_persist(self):
        form = SignUpForm(
            data={
                "username": "deferred",
                "email": "deferred@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "rgpd_accepte": True,
            }
        )

        self.assertTrue(form.is_valid())
        user = form.save(commit=False)

        self.assertIsNone(user.pk)
        self.assertEqual(user.email, "deferred@example.com")
        self.assertTrue(user.rgpd_accepte)
        self.assertIsNotNone(user.rgpd_date_acceptation)
        self.assertFalse(User.objects.filter(username="deferred").exists())


class AccountsPublicViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="john",
            email="john@example.com",
            password="pass1234",
        )

    def test_signup_get_renders_signup_page(self):
        response = self.client.get(reverse("signup"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/signup.html")

    def test_signup_post_valid_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("signup"),
            data={
                "username": "newbie",
                "email": "newbie@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "rgpd_accepte": True,
            },
        )

        self.assertRedirects(response, reverse("login"))
        created = User.objects.get(username="newbie")
        self.assertEqual(created.email, "newbie@example.com")
        self.assertTrue(created.rgpd_accepte)
        self.assertIsNotNone(created.rgpd_date_acceptation)

    def test_signup_post_invalid_returns_form_errors(self):
        response = self.client.post(
            reverse("signup"),
            data={
                "username": "newbie",
                "email": "newbie@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/signup.html")
        self.assertIn("rgpd_accepte", response.context["form"].errors)

    def test_login_get_renders_login_page(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(f"{reverse('login')}?next="))

    def test_profile_get_authenticated_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")

    def test_logout_post_redirects_home(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("home"))

    def test_password_reset_form_get_renders_template(self):
        response = self.client.get(reverse("password_reset"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_form.html")

    def test_password_reset_post_redirects_to_done(self):
        response = self.client.post(reverse("password_reset"), {"email": "john@example.com"})

        self.assertRedirects(response, reverse("password_reset_done"))

    def test_password_reset_done_get_renders_template(self):
        response = self.client.get(reverse("password_reset_done"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_done.html")

    def test_password_reset_confirm_get_with_valid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.get(reverse("password_reset_confirm", args=[uid, token]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_confirm.html")
        self.assertTrue(response.context["validlink"])

    def test_password_reset_confirm_get_with_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        response = self.client.get(reverse("password_reset_confirm", args=[uid, "invalid-token"]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_confirm.html")
        self.assertFalse(response.context["validlink"])

    def test_password_reset_complete_get_renders_template(self):
        response = self.client.get(reverse("password_reset_complete"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_complete.html")


class AccountsAdminViewsTests(TestCase):
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
            username="group_admin",
            email="group_admin@example.com",
            password="pass1234",
        )
        admin_group = Group.objects.create(name="ADMIN")
        self.group_admin_user.groups.add(admin_group)

        self.target_user = User.objects.create_user(
            username="target",
            email="target@example.com",
            password="pass1234",
        )

    def test_user_list_redirects_for_anonymous_and_non_admin(self):
        anonymous_response = self.client.get(reverse("user_admin_list"))
        self.assertEqual(anonymous_response.status_code, 302)
        self.assertTrue(anonymous_response.url.startswith(f"{reverse('login')}?next="))

        self.client.force_login(self.regular_user)
        regular_response = self.client.get(reverse("user_admin_list"))
        self.assertEqual(regular_response.status_code, 302)
        self.assertTrue(regular_response.url.startswith(f"{reverse('login')}?next="))

    def test_user_list_get_for_staff_admin(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("user_admin_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin/user_list.html")
        users = list(response.context["users"])
        self.assertIn(self.target_user, users)
        self.assertEqual(response.context["query"], "")

    def test_user_list_get_for_group_admin(self):
        self.client.force_login(self.group_admin_user)

        response = self.client.get(reverse("user_admin_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin/user_list.html")

    def test_user_list_filters_by_query(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("user_admin_list"), {"q": "target"})

        self.assertEqual(response.status_code, 200)
        users = list(response.context["users"])
        self.assertIn(self.target_user, users)
        self.assertNotIn(self.regular_user, users)
        self.assertEqual(response.context["query"], "target")

    def test_user_edit_get_renders_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("user_admin_edit", args=[self.target_user.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin/user_form.html")
        self.assertEqual(response.context["target"], self.target_user)

    def test_user_edit_post_valid_updates_other_user(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("user_admin_edit", args=[self.target_user.pk]),
            data={
                "username": "target",
                "email": "updated@example.com",
                "is_active": "on",
                "is_staff": "on",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("user_admin_list"))
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.email, "updated@example.com")
        self.assertTrue(self.target_user.is_active)
        self.assertTrue(self.target_user.is_staff)
        self.assertContains(response, "Utilisateur mis a jour.")

    def test_user_edit_post_invalid_returns_errors(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("user_admin_edit", args=[self.target_user.pk]),
            data={
                "username": "",
                "email": "not-an-email",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin/user_form.html")
        self.assertIn("username", response.context["form"].errors)

    def test_user_edit_prevents_self_deactivation(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("user_admin_edit", args=[self.admin_user.pk]),
            data={
                "username": "admin",
                "email": "admin@example.com",
                "is_staff": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Vous ne pouvez pas retirer vos propres droits admin staff ou desactiver votre compte.",
            response.context["form"].non_field_errors(),
        )
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)

    def test_user_edit_prevents_self_staff_removal(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("user_admin_edit", args=[self.admin_user.pk]),
            data={
                "username": "admin",
                "email": "admin@example.com",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Vous ne pouvez pas retirer vos propres droits admin staff ou desactiver votre compte.",
            response.context["form"].non_field_errors(),
        )
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_staff)

    def test_user_edit_allows_self_update_when_keeping_active_and_staff(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("user_admin_edit", args=[self.admin_user.pk]),
            data={
                "username": "admin",
                "email": "new-admin@example.com",
                "is_active": "on",
                "is_staff": "on",
            },
        )

        self.assertRedirects(response, reverse("user_admin_list"))
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.email, "new-admin@example.com")
