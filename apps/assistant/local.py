"""Assistant integre, sans cle API : recherche dans les contenus de la JEC et repond uniquement avec eux."""
import math
import re
import unicodedata

from apps.content.models import Definition
from apps.federations.models import Federation, Leader

from .knowledge import CONTACT, chunks

STOP = set("""le la les un une des de du d l et ou a au aux en dans sur pour par avec sans ce cet cette ces que qui quoi quel quelle quels
quelles est sont etre ete suis es sommes etes sera ont avoir il elle ils elles on nous vous je tu me te se leur leurs mon ma mes ton ta tes son sa
ses notre nos votre vos y ne pas plus comment pourquoi quand combien dit dites svp stp merci bonjour salut bonsoir hello peut peux pouvez veux
voudrais faire fait donne donnez parle parlez moi explique expliquez savoir connaitre sais dire quoi""".split())

STOP |= set("passe passent deroule deroulent fonctionne fonctionnent marche sert servent existe existent faut doit font procede fonctionnement".split())

REFUSAL = ("Je suis l'assistant de la JEC : je ne peux répondre qu'aux questions concernant la JEC, et je n'ai pas trouvé d'information "
           "correspondante dans notre documentation.\n\nVous pouvez par exemple me demander : « Qu'est-ce que la JEC ? », « Quelles sont les "
           "fédérations ? » ou « Que signifie Voir – Réfléchir – Agir ? ». Pour une autre demande, écrivez-nous via la page Contact.")
_idx = {"id": None}
DEF_INTENT = re.compile(r"(qu.?est.?ce (que|qu)|c.?est quoi|que signifie|signification|definition|definir|veut dire|explique|qui est|que represente|que symbolise)")
OFFTOPIC = re.compile(r"(capitale|recette|meteo|football|match de|bitcoin|traduis|python|javascript|programme informatique|combien font|president de la republique|ministre|elections?|prix du|horoscope|blague|film|chanson de)")
ANCHORS = {"jec", "jecist", "jeci", "mouvem", "federa", "section", "militan", "conseil", "equipe"}
SYN = {"mvt": "mouvement", "mvts": "mouvement", "mouvements": "mouvement", "types": "identite dimension", "type": "identite dimension",
       "sortes": "identite", "categories": "identite", "nature": "identite", "natures": "identite", "valeurs": "mission identite",
       "but": "mission", "buts": "mission", "objectif": "mission", "objectifs": "mission", "vocation": "mission", "role": "mission",
       "histoire": "historique genese", "origine": "historique genese", "origines": "historique genese", "creation": "historique genese",
       "fondation": "historique genese", "fonde": "historique genese", "naissance": "historique genese", "fondateur": "historique genese",
       "uniforme": "tenues", "habit": "tenues", "vetement": "tenues", "drapeau": "etendard", "chanson": "chants hymne", "cantique": "chants",
       "structure": "structuration", "organisation": "structuration", "hierarchie": "structuration", "niveaux": "structuration",
       "president": "coordonnateur", "chef": "coordonnateur", "methode": "voir reflechir agir", "devise": "voir reflechir agir",
       "fed": "federation", "feds": "federation", "doc": "document", "docs": "document", "resp": "responsable", "sec": "section",
       "cellule": "section", "cellules": "section", "jeciste": "jec", "jecistes": "jec", "evenement": "activites", "evenements": "activites"}


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def tokens(s):
    return [w[:6] for w in re.findall(r"[a-z0-9]+", norm(s)) if len(w) > 2 and w not in STOP]


def qtokens(s):
    """Mots de la question + synonymes et abreviations courantes (mvt = mouvement, types = identite...)."""
    words = re.findall(r"[a-z0-9]+", norm(s))
    return tokens(" ".join(words + [SYN[w] for w in words if w in SYN]))


def _index():
    cs = chunks()
    if _idx["id"] is not id(cs):
        sets = [set(tokens(t + " " + x)) for t, x, _ in cs]
        df = {}
        for s in sets:
            for w in s:
                df[w] = df.get(w, 0) + 1
        _idx.update(id=id(cs), sets=sets, titles=[set(tokens(t)) for t, _, _ in cs], df=df)
    return cs, _idx


def search(q):
    cs, ix = _index()
    qt = set(qtokens(q))
    if not qt:
        return []
    n = len(cs)
    idf = lambda w: math.log((n + 1) / (ix["df"].get(w, 0) + 1)) + 1
    total = sum(idf(w) for w in qt)
    res = []
    for (title, text, url), ts, tt in zip(cs, ix["sets"], ix["titles"]):
        m = qt & ts
        if m:
            base = sum(idf(w) for w in m)
            res.append(((base + sum(idf(w) for w in qt & tt)) * (1.25 if title.startswith("Définition") else 1), base / total, title, text, url))
    return sorted(res, reverse=True)


def _excerpt(text, n=650):
    if len(text) <= n:
        return text
    cut = text[:n]
    i = max(cut.rfind(". "), cut.rfind("\n"))
    return (cut[:i + 1] if i > n // 2 else cut) + " …"


def match_definition(q):
    """Definition du glossaire qui correspond a TOUTE la question (sinon None)."""
    nq = re.sub(r"\bmvts?\b", "mouvement", norm(q))
    qtok = set(tokens(nq))
    best = None
    for d in Definition.objects.filter(is_archived=False):
        for a in d.alias_list:
            na = norm(a)
            if len(na) >= 3 and re.search(r"(?<![a-z0-9])" + re.escape(na) + r"(?![a-z0-9])", nq):
                rest = {w for w in qtok - set(tokens(na)) - {"jec"} if _index()[1]["df"].get(w, 0) > 0}  # mots inconnus du site : ignores
                if not rest and (best is None or len(na) > best[0]):
                    best = (len(na), d)
    return best[1] if best else None


def _format(items):
    return "Voici ce que dit notre documentation :\n\n" + "\n\n".join(f"{t}\n{_excerpt(x)}\nPour en savoir plus : {u}" for t, x, u in items)


def answer(q):
    n, qt = norm(q), set(qtokens(q))
    if not set(tokens(q)):
        return "Bonjour ! Je suis l'assistant de la JEC. Que souhaitez-vous savoir sur le mouvement, ses fédérations, ses activités ou ses documents ?"
    if qt <= {"federa", "jec"} and "federa" in qt and not DEF_INTENT.search(n):
        fs = list(Federation.objects.filter(is_active=True))
        if fs:
            return (f"La JEC compte {len(fs)} fédérations : " + ", ".join(f.name for f in fs) +
                    ".\n\nPour en savoir plus sur l'une d'elles (équipe, sections), indiquez son nom ou voyez /federations/")
    d = match_definition(q)
    if d and (DEF_INTENT.search(n) or len(set(tokens(q))) <= 3):
        return f"{d.term}\n{d.definition}\nSource : {d.source}\nPour en savoir plus : /glossaire/"
    if re.search(r"(qu.?est.?ce que la jec|c.?est quoi la jec|qui est la jec|qui sommes.nous|presentation de la jec|definition de la jec)", n):
        top = [c for c in chunks() if c[0].startswith("Présentation du mouvement")][:2]
        if top:
            return _format(top)
    if re.search(r"(contact|telephone|numero|e.?mail|courriel|adresse|siege|whatsapp|joindre|appeler)", n):
        return "Pour contacter la JEC :\n" + CONTACT + "\nPour en savoir plus : /contact/"
    if re.search(r"(rejoindre|adherer|adhesion|inscrire|integrer|devenir membre|faire partie)", n):
        return ("Pour rejoindre la JEC, écrivez-nous via la page Contact du site (ou par WhatsApp / e-mail) en indiquant votre établissement et votre ville : "
                "l'équipe vous mettra en relation avec la fédération ou la section la plus proche.\n\n" + CONTACT + "\nPour en savoir plus : /contact/")
    if re.search(r"(equipe nationale|bureau national|responsables nationaux)", n):
        t = Leader.objects.filter(federation__isnull=True, is_archived=False)
        if t:
            return "L'équipe nationale de la JEC :\n" + "\n".join(f"- {l.full_name} : {l.title}" for l in t) + "\nPour en savoir plus : /federations/equipe-nationale/"
    if not (qt & ANCHORS) and OFFTOPIC.search(n):
        return REFUSAL
    res = search(q)
    anchored = bool(qt & ANCHORS)
    if not res or (res[0][1] < 0.55 and not anchored):
        return REFUSAL
    picked, seen = [], set()
    for sc, cov, title, text, url in res:
        if title not in seen and sc >= (0.5 if anchored else 0.6) * res[0][0] and len(picked) < 3:
            picked.append((title, text, url))
            seen.add(title)
    if res[0][1] < 0.55:
        return "Je n'ai pas trouvé de passage qui réponde exactement à votre question ; voici les extraits les plus proches dans notre documentation :\n\n" + _format(picked)[len("Voici ce que dit notre documentation :\n\n"):]
    return _format(picked)
