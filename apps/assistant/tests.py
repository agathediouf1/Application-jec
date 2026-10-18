import json
from unittest import mock

try:  # selon la version du SDK Anthropic
    import httpx2 as httpx
except ImportError:
    import httpx
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from . import views
from .knowledge import build_knowledge


class AssistantTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("import_federations", verbosity=0)
        call_command("import_content", verbosity=0)

    def setUp(self):
        cache.clear()

    def post(self, msgs):
        return self.client.post(reverse("assistant"), json.dumps({"messages": msgs}), content_type="application/json")

    def ask(self, q):
        return self.post([{"role": "user", "content": q}]).json()["reply"]

    @override_settings(ANTHROPIC_API_KEY="")
    def test_works_without_api_key(self):
        self.assertIn("Dakar", self.ask("Quelles sont les fédérations ?"))
        self.assertIn("+221 77 803 37 71", self.ask("Quel est votre numéro de téléphone ?"))
        self.assertNotIn("je ne peux répondre", self.ask("Que signifie Voir Réfléchir Agir ?"))
        self.assertIn("Chantons", self.ask("Quelles sont les paroles de l'hymne de la JEC ?"))
        self.assertIn("Bonjour", self.ask("Bonjour"))

    @override_settings(ANTHROPIC_API_KEY="")
    def test_understands_abbreviations_and_gives_links(self):
        r = self.ask("les types de mvt de la jec")
        self.assertNotIn("je ne peux répondre", r)
        self.assertRegex(r, r"[ÉE]vang")
        self.assertIn("Pour en savoir plus : /", r)
        self.assertNotIn("je ne peux répondre", self.ask("c'est quoi la mission de la jec ?"))
        self.assertNotIn("je ne peux répondre", self.ask("l'histoire de la jec au Sénégal"))

    @override_settings(ANTHROPIC_API_KEY="", LLM_API_KEY="k", LLM_BASE_URL="https://llm.example/v1", LLM_MODEL="m")
    def test_openai_compatible_provider(self):
        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return json.dumps({"choices": [{"message": {"content": "Réponse IA"}}]}).encode()
        with mock.patch.object(views.urllib.request, "urlopen", return_value=Resp()) as m:
            r = self.post([{"role": "user", "content": "Parle-moi de la JEC"}]).json()
        self.assertEqual((r["reply"], r["mode"]), ("Réponse IA", "ai"))
        sent = json.loads(m.call_args[0][0].data)
        self.assertEqual(sent["model"], "m")
        self.assertIn("UNIQUEMENT", sent["messages"][0]["content"])

    @override_settings(ANTHROPIC_API_KEY="")
    def test_gives_definitions_written_in_the_project(self):
        cases = {"c'est quoi le foulard ?": "signe distinctif", "Qu'est-ce que la JECI ?": "1954", "que signifie voir réfléchir agir": "Voir :",
                 "définition du CIDI": "Centre International", "les types de mvt de la jec": "Mouvement d'Étudiant",
                 "c est quoi l'étendard": "drapeau", "que représente la croix du logo": "centralité du Christ"}
        for q, expected in cases.items():
            self.assertIn(expected, self.ask(q), q)

    @override_settings(ANTHROPIC_API_KEY="")
    def test_specific_federation_question_is_not_hijacked_by_a_definition(self):
        r = self.ask("Qui sont les responsables de la fédération de Thiès ?")
        self.assertIn("Thiès", r)
        self.assertNotIn("Section regroupe", r)

    @override_settings(ANTHROPIC_API_KEY="")
    def test_off_topic_is_refused_without_api_key(self):
        for q in ("Quelle est la capitale du Sénégal ?", "Quelle est la capitale de la France ?", "Donne-moi une recette de thiéboudienne", "Écris-moi un programme Python"):
            self.assertIn("je ne peux répondre", self.ask(q), q)

    @override_settings(ANTHROPIC_API_KEY="k")
    def test_falls_back_to_local_when_ai_fails(self):
        with mock.patch.object(views, "call_model", side_effect=RuntimeError("panne")):
            self.assertIn("Dakar", self.ask("Quelles sont les fédérations ?"))

    @override_settings(ANTHROPIC_API_KEY="k")
    def test_invalid_messages(self):
        self.assertEqual(self.post([]).status_code, 400)
        self.assertEqual(self.post([{"role": "system", "content": "x"}]).status_code, 400)

    @override_settings(ANTHROPIC_API_KEY="k")
    def test_reply(self):
        with mock.patch.object(views, "call_model", return_value="Réponse JEC") as m:
            r = self.post([{"role": "assistant", "content": "Salut"}, {"role": "user", "content": "Qu'est-ce que la JEC ?"}])
        self.assertEqual(r.json()["reply"], "Réponse JEC")
        self.assertEqual(m.call_args[0][0][0]["role"], "user")

    @override_settings(ANTHROPIC_API_KEY="k")
    def test_rate_limit(self):
        with mock.patch.object(views, "call_model", return_value="ok"):
            codes = [self.post([{"role": "user", "content": "q"}]).status_code for _ in range(21)]
        self.assertEqual(codes[:20], [200] * 20)
        self.assertEqual(codes[20], 429)

    def test_knowledge_comes_from_the_site(self):
        k = build_knowledge(force=True)
        for needle in ("Dakar", "Formation sur les bases du mouvement", "Voir", "ycs.jecsenegal@gmail.com"):
            self.assertIn(needle, k)

    @override_settings(ANTHROPIC_API_KEY="k", ANTHROPIC_MODEL="claude-haiku-5-5")
    def test_request_sent_to_api_is_well_formed(self):
        seen = {}

        def handler(request):
            seen.update(json.loads(request.content))
            return httpx.Response(200, json={"id": "m", "type": "message", "role": "assistant", "model": "x", "stop_reason": "end_turn",
                                             "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1},
                                             "content": [{"type": "text", "text": "Bonjour"}]})
        import anthropic
        client = anthropic.Anthropic(api_key="k", http_client=httpx.Client(transport=httpx.MockTransport(handler)))
        self.assertEqual(views.call_model([{"role": "user", "content": "Salut"}], client=client), "Bonjour")
        self.assertEqual(seen["model"], "claude-haiku-5-5")
        self.assertIn("UNIQUEMENT", seen["system"][0]["text"])
        self.assertEqual(seen["system"][1]["cache_control"], {"type": "ephemeral"})
