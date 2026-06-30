from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from .models import TrackerItem
from .forms import TrackerItemForm


def _period_start(period: str):
    """
    Retourne (period_norm, start_datetime) pour filtrer.
    start_datetime peut etre None pour "tout" (aucun filtre de date).
    Compatible avec anciens codes: 7d/30d/365d.
    """
    now = timezone.localtime(timezone.now())
    tz = timezone.get_current_timezone()

    # rétro-compat
    if period in (None, "", "30d"):
        period = "month"
    if period == "7d":
        period = "week"
    if period == "365d":
        period = "year"
    if period == "90d":
        period = "quarter"
    if period in ("all", "tout"):
        period = "all"

    if period == "week":
        # début de semaine (lundi 00:00)
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        return "week", start

    if period == "month":
        # 1er du mois 00:00
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return "month", start

    if period == "quarter":
        # début du trimestre courant (jan/avr/juil/oct) 00:00
        quarter_start_month = ((now.month - 1) // 3) * 3 + 1
        start_naive = datetime(now.year, quarter_start_month, 1, 0, 0, 0)
        start = timezone.make_aware(start_naive, tz)
        return "quarter", start

    if period == "year":
        # 1er janvier 00:00
        start_naive = datetime(now.year, 1, 1, 0, 0, 0)
        start = timezone.make_aware(start_naive, tz)
        return "year", start

    if period == "all":
        return "all", None

    # fallback “mois”
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return "month", start


@require_GET
@login_required
def tracker_list(request):
    period_raw = request.GET.get("period", "month")
    period, start = _period_start(period_raw)

    items = TrackerItem.objects.filter(user=request.user)
    if start is not None:
        items = items.filter(date_saisie__gte=start)
    items = items.select_related("emotion__base").order_by("-date_saisie")
    return render(request, "emotions/tracker_list.html", {"items": items, "period": period})


@require_http_methods(["GET", "POST"])
@login_required
def tracker_create(request):
    if request.method == "POST":
        form = TrackerItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            return redirect("tracker_list")
    else:
        form = TrackerItemForm()

    return render(request, "emotions/tracker_form.html", {
        "form": form,
        "mode": "create",
    })


@require_http_methods(["GET", "POST"])
@login_required
def tracker_update(request, pk):
    item = get_object_or_404(TrackerItem, pk=pk, user=request.user)

    if request.method == "POST":
        form = TrackerItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect("tracker_list")
    else:
        form = TrackerItemForm(instance=item)

    return render(request, "emotions/tracker_form.html", {
        "form": form,
        "mode": "edit",
        "item": item,
    })


@require_http_methods(["GET", "POST"])
@login_required
def tracker_delete(request, pk):
    item = get_object_or_404(TrackerItem, pk=pk, user=request.user)

    if request.method == "POST":
        item.delete()
        return redirect("tracker_list")

    return render(request, "emotions/tracker_delete.html", {"item": item})


@require_GET
@login_required
def tracker_report(request):
    period_raw = request.GET.get("period", "month")
    period, start = _period_start(period_raw)

    qs = TrackerItem.objects.filter(user=request.user)
    if start is not None:
        qs = qs.filter(date_saisie__gte=start)
    qs = qs.select_related("emotion__base")

    by_base = qs.values("emotion__base__libelle").annotate(
        nb=Count("id"),
        avg_int=Avg("intensite"),
    ).order_by("-nb")

    by_emotion = qs.values("emotion__base__libelle", "emotion__libelle").annotate(
        nb=Count("id")
    ).order_by("-nb")

    return render(request, "emotions/report.html", {
        "period": period,
        "by_base": by_base,
        "by_emotion": by_emotion,
    })
