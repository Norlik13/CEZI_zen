from django.shortcuts import get_object_or_404, render

from .models import PageInformation

LEGAL_PAGE_SLUGS = {"mentions-legales", "donnees-personnelles", "contact"}


def _published_articles(limit=None):
    qs = (
        PageInformation.objects
        .filter(statut="publie")
        .exclude(slug__in=LEGAL_PAGE_SLUGS)
        .order_by("-date_publication", "-date_mise_a_jour")
    )
    if limit is not None:
        return qs[:limit]
    return qs


def home(request):
    context = {
        "show_tracker": True,
        "page_heading": "Bienvenue sur CESIZen",
        "latest_articles": _published_articles(limit=4),
    }
    return render(request, "infos/home.html", context)


def articles(request):
    context = {
        "show_tracker": False,
        "page_heading": "Articles",
        "latest_articles": _published_articles(),
    }
    return render(request, "infos/home.html", context)


def page_detail(request, slug):
    page = get_object_or_404(PageInformation, slug=slug, statut="publie")
    return render(request, "infos/page_detail.html", {"page": page})
