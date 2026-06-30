from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_http_methods

from accounts.permissions import is_admin
from .models import EmotionBase, Emotion
from .forms import EmotionBaseForm, EmotionForm


@require_GET
@user_passes_test(is_admin)
def base_list(request):
    bases = EmotionBase.objects.all().order_by("libelle")
    return render(request, "emotions/admin/base_list.html", {"bases": bases})


@require_http_methods(["GET", "POST"])
@user_passes_test(is_admin)
def base_create(request):
    if request.method == "POST":
        form = EmotionBaseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("base_list")
    else:
        form = EmotionBaseForm()
    return render(request, "emotions/admin/base_form.html", {"form": form, "mode": "create"})


@require_http_methods(["GET", "POST"])
@user_passes_test(is_admin)
def base_update(request, pk):
    base = get_object_or_404(EmotionBase, pk=pk)
    if request.method == "POST":
        form = EmotionBaseForm(request.POST, instance=base)
        if form.is_valid():
            form.save()
            return redirect("base_list")
    else:
        form = EmotionBaseForm(instance=base)
    return render(request, "emotions/admin/base_form.html", {"form": form, "mode": "edit", "base": base})


@require_http_methods(["GET", "POST"])
@user_passes_test(is_admin)
def base_delete(request, pk):
    base = get_object_or_404(EmotionBase, pk=pk)
    if request.method == "POST":
        base.delete()
        return redirect("base_list")
    return render(request, "emotions/admin/base_delete.html", {"base": base})


@require_GET
@user_passes_test(is_admin)
def emotion_list(request):
    base_id = request.GET.get("base")
    qs = Emotion.objects.select_related("base").order_by("base__libelle", "libelle")
    if base_id:
        qs = qs.filter(base_id=base_id)

    bases = EmotionBase.objects.order_by("libelle")
    return render(request, "emotions/admin/emotion_list.html", {
        "emotions": qs,
        "bases": bases,
        "base_id": base_id,
    })


@require_http_methods(["GET", "POST"])
@user_passes_test(is_admin)
def emotion_create(request):
    if request.method == "POST":
        form = EmotionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("emotion_list")
    else:
        form = EmotionForm()
    return render(request, "emotions/admin/emotion_form.html", {"form": form, "mode": "create"})


@require_http_methods(["GET", "POST"])
@user_passes_test(is_admin)
def emotion_update(request, pk):
    emo = get_object_or_404(Emotion, pk=pk)
    if request.method == "POST":
        form = EmotionForm(request.POST, instance=emo)
        if form.is_valid():
            form.save()
            return redirect("emotion_list")
    else:
        form = EmotionForm(instance=emo)
    return render(request, "emotions/admin/emotion_form.html", {"form": form, "mode": "edit", "emo": emo})


@require_http_methods(["GET", "POST"])
@user_passes_test(is_admin)
def emotion_delete(request, pk):
    emo = get_object_or_404(Emotion, pk=pk)
    if request.method == "POST":
        emo.delete()
        return redirect("emotion_list")
    return render(request, "emotions/admin/emotion_delete.html", {"emo": emo})
