from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import SignUpForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("login")


@login_required
def profile(request):
    return render(request, "accounts/profile.html")