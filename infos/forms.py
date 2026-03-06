from django import forms
from django.utils.text import slugify
from .models import PageInformation


class PageInformationForm(forms.ModelForm):
    class Meta:
        model = PageInformation
        fields = ["titre", "slug", "contenu", "statut", "date_publication"]

    def clean_slug(self):
        slug = self.cleaned_data.get("slug", "")
        titre = self.cleaned_data.get("titre", "")
        if not slug and titre:
            return slugify(titre)
        return slug
