from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from .models import Federation, Leader


class FederationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("import_federations", verbosity=0)

    def test_import_is_complete_and_idempotent(self):
        call_command("import_federations", verbosity=0)
        self.assertEqual(Federation.objects.count(), 8)
        self.assertEqual(Leader.objects.filter(federation__isnull=True).count(), 11)

    def test_public_pages(self):
        for url in (reverse("home"), reverse("federations:list"), reverse("federations:national"),
                    reverse("federations:detail", args=["dakar"])):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_archived_leader_is_hidden(self):
        leader = Leader.objects.filter(federation__slug="dakar", category="team").first()
        leader.is_archived = True
        leader.save()
        r = self.client.get(reverse("federations:detail", args=["dakar"]))
        self.assertNotContains(r, leader.full_name)

    def test_admin_requires_login(self):
        r = self.client.get(reverse("admin:index"))
        self.assertEqual(r.status_code, 302)

    def test_federation_leader_is_scoped_to_own_federation(self):
        dakar, thies = Federation.objects.get(slug="dakar"), Federation.objects.get(slug="thies")
        u = User.objects.create_user("resp", password="x", is_staff=True, role="federation_leader", federation=dakar)
        u.user_permissions.set(Permission.objects.filter(content_type__app_label="federations"))
        self.client.force_login(u)
        r = self.client.get(reverse("admin:federations_leader_changelist"))
        self.assertEqual({o.federation_id for o in r.context["cl"].result_list}, {dakar.id})
        other = Leader.objects.filter(federation=thies).first()
        r = self.client.get(reverse("admin:federations_leader_change", args=[other.pk]))
        self.assertEqual(r.status_code, 302)  # refusé : hors périmètre
