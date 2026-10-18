from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render

from .models import Federation, Leader


def federation_list(request):
    return render(request, "federations/list.html", {"federations": Federation.objects.filter(is_active=True).annotate(n=Count("sections", filter=Q(sections__is_archived=False)))})


def federation_detail(request, slug):
    fed = get_object_or_404(Federation, slug=slug, is_active=True)
    leaders = fed.leaders.filter(is_archived=False)
    return render(request, "federations/detail.html", {
        "fed": fed,
        "coordinators": leaders.filter(category=Leader.Category.COORD),
        "team": leaders.filter(category=Leader.Category.TEAM),
        "sections": fed.sections.filter(is_archived=False),
    })


def national_team(request):
    team = Leader.objects.filter(federation__isnull=True, is_archived=False)
    return render(request, "federations/national.html", {"team": team})
