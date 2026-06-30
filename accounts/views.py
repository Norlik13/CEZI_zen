from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import SignUpForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_http_methods


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("login")


@require_http_methods(["GET", "POST"])
@login_required
def profile(request):
    password_form = PasswordChangeForm(user=request.user, data=request.POST or None)
    password_changed = False

    if request.method == "POST" and password_form.is_valid():
        password_form.save()
        update_session_auth_hash(request, request.user)
        password_changed = True

    return render(
        request,
        "accounts/profile.html",
        {
            "password_form": password_form,
            "password_changed": password_changed,
        },
    )
