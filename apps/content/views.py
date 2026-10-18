import datetime
import os
from functools import lru_cache

from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Q
from django.templatetags.static import static
from django.shortcuts import get_object_or_404, redirect, render

from apps.federations.models import Federation, Leader, Section

from .forms import ContactForm
from .models import Activity, Article, Definition, Document, Photo


def _slides():
    """Diaporama d'accueil : photos de l'album Accueil ; sinon les deux photos fournies avec le site."""
    s = [{"url": p.file.url, "title": p.title} for p in Photo.objects.filter(album__iexact="Accueil", is_archived=False).order_by("id") if p.kind == "image"]
    return s or [{"url": static("images/slides/accueil-1.jpg"), "title": "Jécistes réunis devant Notre-Dame de la Miséricorde"},
                 {"url": static("images/slides/accueil-2.jpg"), "title": "Les jécistes en célébration"}]


def home(request):
    return render(request, "core/home.html", {
        "federations": Federation.objects.filter(is_active=True).annotate(n=Count("sections", filter=Q(sections__is_archived=False))),
        "slides": _slides(),
        "stats": [("Fédérations", Federation.objects.filter(is_active=True).count()),
                  ("Sections", Section.objects.filter(is_archived=False).count()),
                  ("Responsables", Leader.objects.filter(is_archived=False).count()),
                  ("Documents", Document.objects.filter(is_archived=False).count())],
        "news": Article.objects.filter(is_archived=False)[:3],
        "upcoming": Activity.objects.filter(is_archived=False, date__gte=datetime.date.today())[:3],
    })


def about(request):
    return render(request, "content/about.html", {"team": Leader.objects.filter(federation__isnull=True, is_archived=False)})


def activities(request):
    qs = Activity.objects.filter(is_archived=False)
    today = datetime.date.today()
    return render(request, "content/activities.html", {"upcoming": qs.filter(date__gte=today), "past": qs.filter(date__lt=today).order_by("-date")})


def news(request):
    return render(request, "content/news.html", {"articles": Article.objects.filter(is_archived=False)})


def gallery(request):
    return render(request, "content/gallery.html", {"photos": Photo.objects.filter(is_archived=False), "drive": settings.DRIVE_ALBUM_URL})


def documents(request):
    q, cat = request.GET.get("q", "").strip(), request.GET.get("cat", "")
    qs = Document.objects.filter(is_archived=False)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if cat:
        qs = qs.filter(category=cat)
    return render(request, "content/documents.html", {"docs": qs, "q": q, "cat": cat, "cats": Document.CATS})


@lru_cache(maxsize=32)
def _docx_html(path, mtime):
    import mammoth
    with open(path, "rb") as fh:
        return mammoth.convert_to_html(fh).value


def document(request, pk):
    doc = get_object_or_404(Document, pk=pk, is_archived=False)
    preview = ""
    if doc.file and doc.ext == "docx" and not doc.body:
        try:
            preview = _docx_html(doc.file.path, os.path.getmtime(doc.file.path))
        except Exception:
            preview = ""
    return render(request, "content/document.html", {"doc": doc, "preview": preview})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Merci ! Votre message a bien été enregistré. Nous vous répondrons rapidement.")
        return redirect("contact")
    return render(request, "content/contact.html", {"form": form})


def glossary(request):
    return render(request, "content/glossary.html", {"defs": Definition.objects.filter(is_archived=False)})


# ---------- Application mobile (QR code + PWA) ----------
def qr_code(request, ext):
    import io

    import segno
    from django.http import HttpResponse
    from .context import site_url
    buf = io.BytesIO()
    segno.make(site_url(request), error="m").save(buf, kind=ext, scale=10, border=2, dark="#0A2D6B", **({"xmldecl": False} if ext == "svg" else {}))
    return HttpResponse(buf.getvalue(), content_type="image/svg+xml" if ext == "svg" else "image/png")


def manifest(request):
    from django.http import JsonResponse
    ic = lambda f, s, p="any": {"src": static("images/pwa/" + f), "sizes": f"{s}x{s}", "type": "image/png", "purpose": p}
    return JsonResponse({"name": "JEC Sénégal", "short_name": "JEC", "description": "Jeunesse Étudiante Catholique du Sénégal", "lang": "fr",
                         "start_url": "/?source=app", "scope": "/", "display": "standalone", "background_color": "#ffffff", "theme_color": "#1E6FD9",
                         "icons": [ic("icon-192.png", 192), ic("icon-512.png", 512), ic("icon-maskable-512.png", 512, "maskable")]},
                        content_type="application/manifest+json")


def service_worker(request):
    from django.http import HttpResponse
    r = HttpResponse((settings.BASE_DIR / "templates" / "pwa" / "sw.js").read_text(encoding="utf-8"), content_type="application/javascript")
    r["Service-Worker-Allowed"] = "/"
    r["Cache-Control"] = "no-cache"
    return r


def offline(request):
    return render(request, "content/offline.html")
