NAV = [("home", "Accueil"), ("about", "Qui sommes-nous ?"), ("federations:list", "Fédérations"), ("activities", "Activités"),
       ("news", "Actualités"), ("gallery", "Galerie"), ("documents", "Documentation"), ("contact", "Contact")]


def nav(request):
    from django.urls import reverse
    items = []
    for name, label in NAV:
        url = reverse(name)
        active = request.path == url if url == "/" else request.path.startswith(url)
        items.append({"url": url, "label": label, "active": active})
    from django.conf import settings
    return {"nav_items": items, "drive_url": settings.DRIVE_ALBUM_URL, "site_url": site_url(request),
            "qr_is_local": not settings.SITE_URL and request.get_host().split(":")[0] in ("localhost", "127.0.0.1", "[::1]", "0.0.0.0")}


def site_url(request):
    """Adresse que le QR code encode : SITE_URL (recommande) sinon l'adresse utilisee pour consulter le site."""
    from django.conf import settings
    return (settings.SITE_URL or request.build_absolute_uri("/")).rstrip("/") + "/"
