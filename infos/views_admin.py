from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from accounts.permissions import is_admin
from .models import PageInformation
from .forms import PageInformationForm


@user_passes_test(is_admin)
def page_list(request):
    pages = PageInformation.objects.all().order_by("-date_mise_a_jour")
    return render(request, "infos/admin/page_list.html", {"pages": pages})


@user_passes_test(is_admin)
def page_create(request):
    if request.method == "POST":
        form = PageInformationForm(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            # si publié sans date, on la met
            if page.statut == "publie" and not page.date_publication:
                page.date_publication = timezone.now()
            page.save()
            return redirect("page_admin_list")
    else:
        form = PageInformationForm()

    return render(request, "infos/admin/page_form.html", {"form": form, "mode": "create"})


@user_passes_test(is_admin)
def page_update(request, pk):
    page = get_object_or_404(PageInformation, pk=pk)

    if request.method == "POST":
        form = PageInformationForm(request.POST, instance=page)
        if form.is_valid():
            page = form.save(commit=False)
            if page.statut == "publie" and not page.date_publication:
                page.date_publication = timezone.now()
            page.save()
            return redirect("page_admin_list")
    else:
        form = PageInformationForm(instance=page)

    return render(request, "infos/admin/page_form.html", {"form": form, "mode": "edit", "page": page})


@user_passes_test(is_admin)
def page_delete(request, pk):
    page = get_object_or_404(PageInformation, pk=pk)

    if request.method == "POST":
        page.delete()
        return redirect("page_admin_list")

    return render(request, "infos/admin/page_delete.html", {"page": page})