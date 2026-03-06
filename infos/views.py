from django.shortcuts import render, get_object_or_404
from .models import Menu, PageInformation

def home(request):
    menus = Menu.objects.filter(actif=True).prefetch_related("entrees").order_by("ordre")
    return render(request, "infos/home.html", {"menus": menus})

def page_detail(request, slug):
    page = get_object_or_404(PageInformation, slug=slug, statut="publie")
    return render(request, "infos/page_detail.html", {"page": page})
