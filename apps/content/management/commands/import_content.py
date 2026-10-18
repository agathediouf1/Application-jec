import json
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from apps.content.models import Definition, Document

DATA = Path(__file__).resolve().parents[2] / "data"


class Command(BaseCommand):
    help = "Importe les 21 documents du site d'origine (fiches consultables et fichiers)."

    def handle(self, *args, **opts):
        for d in json.loads((DATA / "documents.json").read_text(encoding="utf-8")):
            f = d.pop("file", None)
            doc, _ = Document.objects.update_or_create(title=d["title"], defaults=d)
            if f and not doc.file:
                with open(DATA / "docs" / f, "rb") as fh:
                    doc.file.save(f, File(fh), save=True)
        for g in json.loads((DATA / "glossary.json").read_text(encoding="utf-8")):
            Definition.objects.get_or_create(term=g["term"], defaults=g)
        self.stdout.write(self.style.SUCCESS(f"{Document.objects.count()} documents, {Definition.objects.count()} définitions."))
