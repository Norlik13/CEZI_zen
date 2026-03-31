from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    rgpd_accepte = forms.BooleanField(
        required=True,
        label="J'accepte la politique RGPD"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2", "rgpd_accepte")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.rgpd_accepte = True
        user.rgpd_date_acceptation = timezone.now()
        if commit:
            user.save()
        return user


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "email", "is_active", "is_staff")
