"""Base de connaissances de l'assistant : tout vient du site (contenus d'origine + base de donnees)."""
import html
import os
import re
import time
from functools import lru_cache

from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags

from apps.content.models import Activity, Article, Definition, Document
from apps.federations.models import Federation, Leader

FRAGMENTS = [("Présentation du mouvement (identité et mission)", "about_presentation"), ("Signes de la JEC", "about_signes"),
             ("Plan d'action 2025-2028", "act_plan"), ("Rencontres", "act_rencontres"),
             ("Recommandations du Conseil National", "act_recommandations")]
MAX_CHARS = 100_000
_cache = {"t": 0.0, "s": None, "c": None}


@lru_cache(maxsize=64)
def _file_text(path, mtime):
    """Texte d'un document PDF ou Word envoye sur le site (pour que l'assistant le connaisse)."""
    try:
        if path.lower().endswith(".pdf"):
            from pypdf import PdfReader
            return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)[:20000]
        if path.lower().endswith(".docx"):
            import mammoth
            with open(path, "rb") as fh:
                return mammoth.extract_raw_text(fh).value[:20000]
    except Exception:
        pass
    return ""


def _txt(raw):
    raw = raw.replace("{% verbatim %}", "").replace("{% endverbatim %}", "")
    raw = re.sub(r"</(p|li|h[1-6]|div|tr|ul)>|<br\s*/?>", "\n", raw)
    t = html.unescape(strip_tags(raw))
    return re.sub(r"\n\s*\n+", "\n", re.sub(r"[ \t]+", " ", t)).strip()


def sections(force=False):
    """Liste de (titre, texte, adresse de la page) : tout ce que contient le site."""
    if not force and _cache["s"] and time.time() - _cache["t"] < 300:
        return _cache["s"]
    urls = {"about": reverse("about"), "act": reverse("activities")}
    out = [("Plan du site", SITE_MAP.format(drive=settings.DRIVE_ALBUM_URL), "/")]
    for d in Definition.objects.filter(is_archived=False):
        aka = f" (aussi : {d.aliases})" if d.aliases else ""
        out.append((f"Définition : {d.term}", f"{d.term}{aka} : {d.definition}\nSource : {d.source}", reverse("glossary")))
    for title, name in FRAGMENTS:
        u = urls["about"] if name.startswith("about") else urls["act"]
        out.append((title, _txt((settings.BASE_DIR / "templates" / "content" / f"{name}.html").read_text(encoding="utf-8")), u))
    out.append(("Équipe nationale", "\n".join(f"{l.full_name} : {l.title}" for l in Leader.objects.filter(federation__isnull=True, is_archived=False)), reverse("federations:national")))
    for f in Federation.objects.filter(is_active=True):
        lines = [f"{f.name} — {f.tagline}"]
        leaders = f.leaders.filter(is_archived=False)
        c = [l.full_name for l in leaders.filter(category="coord")]
        if c:
            lines.append("Coordonnateurs nationaux : " + ", ".join(c))
        lines += [f"{l.full_name} : {l.title}" for l in leaders.filter(category="team")]
        lines.append("Sections : " + ", ".join(s.name for s in f.sections.filter(is_archived=False)))
        out.append((f.name, "\n".join(lines), f.get_absolute_url()))
    for d in Document.objects.filter(is_archived=False):
        text = _txt(d.body)
        if not text and d.file:
            try:
                text = _file_text(d.file.path, os.path.getmtime(d.file.path))
            except OSError:
                text = ""
        out.append((d.title, f"{d.description}\n{text}", d.get_absolute_url()))
    for a in Activity.objects.filter(is_archived=False):
        out.append((f"Activité : {a.title}", f"{a.date:%d/%m/%Y} {a.place} {a.description}", urls["act"]))
    for a in Article.objects.filter(is_archived=False)[:20]:
        out.append((a.title, f"{a.published:%d/%m/%Y} {a.summary or a.body[:400]}", reverse("news")))
    out.append(("Contact officiel", CONTACT, reverse("contact")))
    _cache.update(t=time.time(), s=out, c=None)
    return out


SITE_MAP = ("Pages du site : Accueil (/), Qui sommes-nous ? (/qui-sommes-nous/ : identité, mission, équipe nationale, signes), "
            "Fédérations (/federations/ et /federations/equipe-nationale/), Activités (/activites/ : calendrier, plan d'action 2025-2028, rencontres, recommandations), "
            "Actualités (/actualites/), Galerie (/galerie/ : photos, vidéos et fichiers), Documentation (/documentation/ : documents officiels à consulter ou télécharger), "
            "Contact (/contact/). Le bouton Connexion donne accès au tableau de bord des responsables. Album photos Google Drive : {drive}")
CONTACT = ("Email : ycs.jecsenegal@gmail.com. Téléphone / WhatsApp : +221 77 803 37 71, +221 78 541 80 70, +221 77 431 21 05. "
           "Siège : Centrale des oeuvres catholiques et apostoliques, 4 allées Papa Guèye Fall, Dakar. La page Contact du site permet d'écrire à l'équipe.")


def build_knowledge(force=False):
    body = "\n".join(f"\n## {t}\n(page : {u})\n{x}" for t, x, u in sections(force))
    return ("# DOCUMENTATION OFFICIELLE DE LA JEC SENEGAL" + body)[:MAX_CHARS]


def chunks(force=False):
    """Morceaux courts (titre, texte, page) utilises par la recherche integree."""
    s = sections(force)
    if _cache["c"] is None:
        out = []
        for title, text, url in s:
            buf = ""
            for line in text.split("\n"):
                if buf and len(buf) + len(line) > 800:
                    out.append((title, buf.strip(), url))
                    buf = ""
                buf += line + "\n"
            if buf.strip():
                out.append((title, buf.strip(), url))
        _cache["c"] = out
    return _cache["c"]
