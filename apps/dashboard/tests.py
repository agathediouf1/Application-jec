import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.content.models import ContactMessage, Document
from apps.federations.models import Federation, Leader


class SiteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("import_federations", verbosity=0)
        call_command("import_content", verbosity=0)

    def test_public_pages(self):
        for n in ("home", "about", "activities", "news", "gallery", "documents", "contact", "federations:list"):
            self.assertEqual(self.client.get(reverse(n)).status_code, 200, n)

    def test_documents_imported_and_viewable(self):
        self.assertGreaterEqual(Document.objects.count(), 21)
        self.assertEqual(self.client.get(reverse("glossary")).status_code, 200)
        self.assertEqual(self.client.get(Document.objects.filter(body__gt="").first().get_absolute_url()).status_code, 200)

    def test_contact_form_saves(self):
        self.client.post(reverse("contact"), {"name": "A", "email": "a@b.sn", "message": "Bonjour"})
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_dashboard_needs_login(self):
        self.assertEqual(self.client.get(reverse("manage:dashboard")).status_code, 302)

    def test_leader_scope_and_archive(self):
        dakar, thies = Federation.objects.get(slug="dakar"), Federation.objects.get(slug="thies")
        u = User.objects.create_user("r", password="x", is_staff=True, role="federation_leader", federation=dakar)
        self.client.force_login(u)
        self.assertEqual(self.client.get(reverse("manage:list", args=["documents"])).status_code, 403)
        r = self.client.post(reverse("manage:add", args=["leaders"]), {"category": "team", "full_name": "Test Nouveau", "title": "Secrétaire", "order": 1, "federation": thies.pk})
        self.assertEqual(r.status_code, 302)
        new = Leader.objects.get(full_name="Test Nouveau")
        self.assertEqual(new.federation_id, dakar.pk)
        other = Leader.objects.filter(federation=thies).first()
        self.assertEqual(self.client.post(reverse("manage:toggle", args=["leaders", other.pk])).status_code, 404)
        self.client.post(reverse("manage:toggle", args=["leaders", new.pk]))
        self.assertNotContains(self.client.get(dakar.get_absolute_url()), "Test Nouveau")


    def test_all_documents_viewable(self):
        for d in Document.objects.all():
            self.assertEqual(self.client.get(d.get_absolute_url()).status_code, 200, d.title)

    def test_gallery_accepts_any_format_but_blocks_executables(self):
        from apps.content.models import Photo
        u = User.objects.create_superuser("adm", "a@b.sn", "x")
        self.client.force_login(u)
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp):
            for name, ok in (("photo.cr2", True), ("clip.mp4", True), ("note.docx", True), ("virus.exe", False)):
                self.client.post(reverse("manage:add", args=["photos"]), {"title": name, "album": "", "file": SimpleUploadedFile(name, b"x" * 20)})
                self.assertEqual(Photo.objects.filter(title=name).exists(), ok, name)
            self.assertEqual(self.client.get(reverse("gallery")).status_code, 200)

    def test_home_has_slider_and_all_federations(self):
        r = self.client.get(reverse("home"))
        self.assertContains(r, 'hero-slide')
        self.assertEqual(len(r.context["federations"]), 8)

    def test_reimport_restores_federations_and_keeps_additions(self):
        dk = Federation.objects.get(slug="dakar")
        dk.is_active = False
        dk.save()
        Leader.objects.create(federation=dk, full_name="Ajout manuel")
        call_command("import_federations", verbosity=0)
        dk.refresh_from_db()
        self.assertTrue(dk.is_active)
        self.assertTrue(Leader.objects.filter(full_name="Ajout manuel").exists())


    def test_qr_code_and_pwa_files(self):
        import segno
        from django.test import override_settings
        r = self.client.get("/application/qr.svg")
        self.assertEqual((r.status_code, r["Content-Type"]), (200, "image/svg+xml"))
        self.assertIn(b"<svg", r.content)
        self.assertEqual(self.client.get("/application/qr.png").content[:4], b"\x89PNG")
        with override_settings(SITE_URL="https://jec.example.sn"):
            import io
            buf = io.BytesIO()
            segno.make("https://jec.example.sn/", error="m").save(buf, kind="svg", scale=10, border=2, dark="#0A2D6B", xmldecl=False)
            self.assertEqual(self.client.get("/application/qr.svg").content, buf.getvalue())
        m = self.client.get("/manifest.webmanifest").json()
        self.assertEqual((m["display"], m["start_url"]), ("standalone", "/?source=app"))
        self.assertEqual({i["sizes"] for i in m["icons"]}, {"192x192", "512x512"})
        sw = self.client.get("/sw.js")
        self.assertEqual(sw["Service-Worker-Allowed"], "/")
        self.assertIn(b"addEventListener", sw.content)
        self.assertEqual(self.client.get("/hors-ligne/").status_code, 200)
        home = self.client.get(reverse("home")).content.decode()
        self.assertIn("data-app-open", home)
        self.assertIn('rel="manifest"', home)
