from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.forms import DateInput, modelform_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.content.models import Activity, Article, ContactMessage, Definition, Document, Photo
from apps.federations.models import Federation, Leader, Section

REG = {
    "leaders": dict(model=Leader, label="Responsables", icon="people-fill", scoped=True, flag="is_archived",
                    fields=["federation", "category", "full_name", "title", "order"], cols=["full_name", "title", "category", "federation"]),
    "sections": dict(model=Section, label="Sections / cellules", icon="building", scoped=True, flag="is_archived",
                     fields=["federation", "name"], cols=["name", "federation"]),
    "documents": dict(model=Document, label="Documents", icon="folder2-open", flag="is_archived",
                      fields=["title", "category", "description", "pages", "file", "url", "body"], cols=["title", "category"]),
    "articles": dict(model=Article, label="Actualités", icon="newspaper", flag="is_archived",
                     fields=["title", "kind", "summary", "body", "image", "published"], cols=["title", "kind", "published"],
                     widgets={"published": DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}),
    "photos": dict(model=Photo, label="Galerie", icon="images", flag="is_archived", fields=["title", "album", "file"], cols=["title", "album"]),
    "activities": dict(model=Activity, label="Activités", icon="calendar-event", flag="is_archived",
                       fields=["title", "description", "date", "place"], cols=["title", "date", "place"],
                       widgets={"date": DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}),
    "definitions": dict(model=Definition, label="Définitions (glossaire)", icon="book", flag="is_archived",
                        fields=["term", "aliases", "definition", "source"], cols=["term", "definition", "source"]),
    "federations": dict(model=Federation, label="Fédérations", icon="map", flag="is_active", invert=True,
                        fields=["name", "slug", "tagline", "emblem", "description"], cols=["name", "tagline"]),
    "messages": dict(model=ContactMessage, label="Messages reçus", icon="envelope-fill", flag="handled", flag_label="Traité",
                     readonly=True, fields=[], cols=["name", "email", "message", "created"]),
}


def cfg_for(request, key):
    cfg = REG.get(key)
    u = request.user
    if not cfg or not u.is_staff or not (u.sees_everything or cfg.get("scoped")):
        raise PermissionDenied
    return cfg


def scoped_qs(u, cfg):
    qs = cfg["model"].objects.all()
    if cfg.get("scoped") and not u.sees_everything:
        qs = qs.filter(federation_id=u.federation_id) if u.federation_id else qs.none()
    return qs


def is_off(obj, cfg):
    v = getattr(obj, cfg["flag"])
    return (not v) if cfg.get("invert") else v


def menu(u):
    return [(k, c["label"], c["icon"]) for k, c in REG.items() if u.sees_everything or c.get("scoped")]


@login_required
def dashboard(request):
    u = request.user
    if not u.is_staff:
        raise PermissionDenied
    cards = []
    for k, c in REG.items():
        if u.sees_everything or c.get("scoped"):
            cards.append({"key": k, "label": c["label"], "icon": c["icon"], "n": sum(1 for o in scoped_qs(u, c) if not is_off(o, c))})
    new_msgs = ContactMessage.objects.filter(handled=False)[:5] if u.sees_everything else []
    return render(request, "manage/dashboard.html", {"cards": cards, "menu": menu(u), "new_msgs": new_msgs, "key": ""})


@login_required
def items(request, key):
    cfg = cfg_for(request, key)
    show_off = request.GET.get("archived") == "1"

    def val(o, c):
        d = getattr(o, f"get_{c}_display", None)
        return d() if d else getattr(o, c)

    rows = [{"o": o, "cells": [val(o, c) for c in cfg["cols"]]} for o in scoped_qs(request.user, cfg)[:300] if is_off(o, cfg) == show_off]
    heads = [cfg["model"]._meta.get_field(c).verbose_name for c in cfg["cols"]]
    return render(request, "manage/list.html", {"cfg": cfg, "key": key, "rows": rows, "heads": heads, "show_off": show_off, "menu": menu(request.user)})


@login_required
def edit(request, key, pk=None):
    cfg = cfg_for(request, key)
    if cfg.get("readonly"):
        raise PermissionDenied
    u = request.user
    limited = cfg.get("scoped") and not u.sees_everything
    obj = get_object_or_404(scoped_qs(u, cfg), pk=pk) if pk else None
    Form = modelform_factory(cfg["model"], fields=[f for f in cfg["fields"] if not (limited and f == "federation")], widgets=cfg.get("widgets"))
    form = Form(request.POST or None, request.FILES or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        o = form.save(commit=False)
        if limited:
            o.federation_id = u.federation_id
        o.save()
        messages.success(request, "Enregistré.")
        return redirect("manage:list", key=key)
    return render(request, "manage/form.html", {"cfg": cfg, "key": key, "form": form, "obj": obj, "menu": menu(u)})


@login_required
@require_POST
def toggle(request, key, pk):
    cfg = cfg_for(request, key)
    obj = get_object_or_404(scoped_qs(request.user, cfg), pk=pk)
    setattr(obj, cfg["flag"], not getattr(obj, cfg["flag"]))
    obj.save(update_fields=[cfg["flag"]])
    messages.success(request, "Mis à jour.")
    return redirect("manage:list", key=key)
