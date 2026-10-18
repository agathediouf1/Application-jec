import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.federations.models import Federation, Leader, Section

DATA = Path(__file__).resolve().parents[2] / "data" / "federations.json"


class Command(BaseCommand):
    help = "Remet les 8 fédérations d'origine (équipes, sections). Ne supprime jamais vos ajouts."

    @transaction.atomic
    def handle(self, *args, **opts):
        data = json.loads(DATA.read_text(encoding="utf-8"))
        for i, p in enumerate(data["national"]):
            Leader.objects.get_or_create(federation=None, full_name=p["name"], defaults={"title": p["poste"], "order": i})
        for f in data["federations"]:
            fed, _ = Federation.objects.update_or_create(slug=f["slug"], defaults={
                "name": f["name"], "tagline": f["tagline"], "emblem": f["emblem"], "is_active": True})
            for i, n in enumerate(f["coordinators"]):
                Leader.objects.get_or_create(federation=fed, category="coord", full_name=n, defaults={"order": i})
            for i, p in enumerate(f["team"]):
                Leader.objects.get_or_create(federation=fed, category="team", full_name=p["name"], defaults={"title": p["poste"], "order": i})
            for n in f["sections"]:
                Section.objects.get_or_create(federation=fed, name=n)
        self.stdout.write(self.style.SUCCESS(f"{Federation.objects.filter(is_active=True).count()} fédérations actives."))
