from django import forms
from .models import TrackerItem, Emotion, EmotionBase


class TrackerItemForm(forms.ModelForm):
    class Meta:
        model = TrackerItem
        fields = ["emotion", "intensite", "commentaire"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["emotion"].queryset = Emotion.objects.filter(
            actif=True, base__actif=True
        ).select_related("base").order_by("base__libelle", "libelle")
        self.fields["intensite"].widget.attrs.update({"min": 0, "max": 10, "step": 1})


class EmotionBaseForm(forms.ModelForm):
    class Meta:
        model = EmotionBase
        fields = ["libelle", "actif"]


class EmotionForm(forms.ModelForm):
    class Meta:
        model = Emotion
        fields = ["base", "libelle", "actif"]
