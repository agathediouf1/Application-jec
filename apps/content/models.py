import datetime

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse


def max_10mb(f):
    if f.size > 10 * 1024 * 1024:
        raise ValidationError("Fichier trop lourd (10 Mo maximum).")


class Document(models.Model):
    CATS = [("statut", "Textes officiels"), ("plan", "Plan & Action"), ("formation", "Formation"),
            ("org", "Organisation"), ("comm", "Communication")]
    title = models.CharField("titre", max_length=200)
    category = models.CharField("catégorie", max_length=20, choices=CATS)
    description = models.TextField(blank=True)
    pages = models.CharField("pages / format", max_length=100, blank=True)
    file = models.FileField("fichier", upload_to="documents/", blank=True, validators=[
        max_10mb, FileExtensionValidator(["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "txt", "jpg", "jpeg", "png"])])
    url = models.URLField("lien externe", blank=True)
    body = models.TextField("contenu (HTML)", blank=True, help_text="Texte consultable sur le site, rédigé par un administrateur.")
    is_archived = models.BooleanField("archivé", default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("document", args=[self.pk])

    @property
    def ext(self):
        return self.file.name.rsplit(".", 1)[-1].lower() if self.file else ""

    @property
    def is_image(self):
        return self.ext in {"jpg", "jpeg", "png"}

    @property
    def is_pdf(self):
        return bool(self.file) and self.file.name.lower().endswith(".pdf")


class Article(models.Model):
    KINDS = [("actualite", "Actualité"), ("temoignage", "Témoignage"), ("communique", "Communiqué")]
    title = models.CharField("titre", max_length=200)
    kind = models.CharField("type", max_length=20, choices=KINDS, default="actualite")
    summary = models.CharField("résumé", max_length=300, blank=True)
    body = models.TextField("contenu")
    image = models.ImageField(upload_to="news/", blank=True)
    published = models.DateField("date de publication", default=datetime.date.today)
    is_archived = models.BooleanField("archivé", default=False)

    class Meta:
        ordering = ["-published", "-id"]

    def __str__(self):
        return self.title


BLOCKED_EXT = {"exe", "bat", "cmd", "com", "msi", "sh", "php", "py", "js", "html", "htm", "svg", "jar", "dll", "scr", "vbs", "ps1"}


def safe_file(f):
    ext = f.name.rsplit(".", 1)[-1].lower()
    if ext in BLOCKED_EXT:
        raise ValidationError("Ce type de fichier n'est pas autorisé pour des raisons de sécurité.")
    if f.size > 100 * 1024 * 1024:
        raise ValidationError("Fichier trop lourd (100 Mo maximum).")


class Photo(models.Model):
    """Élément de galerie : accepte tous les formats (photo, vidéo, audio, document, fichier brut…)."""
    IMG = {"jpg", "jpeg", "png", "gif", "webp", "avif", "bmp"}
    VID = {"mp4", "webm", "mov", "m4v", "ogv"}
    AUD = {"mp3", "wav", "ogg", "m4a"}
    ICONS = {"pdf": "filetype-pdf", "doc": "file-earmark-word-fill", "docx": "file-earmark-word-fill", "xls": "file-earmark-excel-fill",
             "xlsx": "file-earmark-excel-fill", "ppt": "file-earmark-ppt-fill", "pptx": "file-earmark-ppt-fill", "zip": "file-earmark-zip-fill",
             "rar": "file-earmark-zip-fill", "cr2": "camera-fill", "nef": "camera-fill", "arw": "camera-fill", "dng": "camera-fill", "heic": "camera-fill"}
    title = models.CharField("légende", max_length=200)
    album = models.CharField("album (JNJ, camp, conseil…)", max_length=100, blank=True)
    file = models.FileField("fichier (photo, vidéo, document… tous formats)", upload_to="gallery/", validators=[safe_file])
    is_archived = models.BooleanField("archivée", default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title

    @property
    def ext(self):
        return self.file.name.rsplit(".", 1)[-1].lower() if self.file else ""

    @property
    def kind(self):
        e = self.ext
        return "image" if e in self.IMG else "video" if e in self.VID else "audio" if e in self.AUD else "other"

    @property
    def icon(self):
        return self.ICONS.get(self.ext, "file-earmark-fill")


class Activity(models.Model):
    title = models.CharField("titre", max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    place = models.CharField("lieu", max_length=150, blank=True)
    is_archived = models.BooleanField("archivée", default=False)

    class Meta:
        ordering = ["date"]
        verbose_name_plural = "activities"

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    name = models.CharField("nom", max_length=120)
    email = models.EmailField()
    federation = models.CharField("fédération", max_length=120, blank=True)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField("traité", default=False)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} — {self.created:%d/%m/%Y}"


class Definition(models.Model):
    """Glossaire : definitions ecrites dans les documents de la JEC (utilisees par l'assistant)."""
    term = models.CharField("terme", max_length=150, unique=True)
    aliases = models.CharField("autres formulations (separees par des virgules)", max_length=400, blank=True)
    definition = models.TextField("définition")
    source = models.CharField("source (document)", max_length=200, blank=True)
    is_archived = models.BooleanField("archivée", default=False)

    class Meta:
        ordering = ["term"]

    def __str__(self):
        return self.term

    @property
    def alias_list(self):
        return [a.strip() for a in [self.term] + self.aliases.split(",") if a.strip()]
