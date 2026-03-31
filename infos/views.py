from django.shortcuts import render, get_object_or_404
from .models import Menu, MenuEntree, PageInformation

LEGAL_PAGE_SLUGS = {"mentions-legales", "donnees-personnelles"}


def home(request):
    menus = Menu.objects.filter(actif=True).prefetch_related("entrees").order_by("ordre")
    linked_page_ids = MenuEntree.objects.exclude(page__isnull=True).values_list("page_id", flat=True)
    standalone_pages = (
        PageInformation.objects
        .filter(statut="publie")
        .exclude(slug__in=LEGAL_PAGE_SLUGS)
        .exclude(id__in=linked_page_ids)
        .order_by("-date_publication", "-date_mise_a_jour")
    )
    return render(
        request,
        "infos/home.html",
        {"menus": menus, "standalone_pages": standalone_pages},
    )

def page_detail(request, slug):
    page = get_object_or_404(PageInformation, slug=slug, statut="publie")
    return render(request, "infos/page_detail.html", {"page": page})
