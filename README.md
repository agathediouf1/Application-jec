# JEC Sénégal — application Django

Construite à partir de `index2.html` : mêmes pages, mêmes contenus, même identité (bleu / blanc / doré), mais pilotée par une base de données et un **tableau de bord** propre à l'application (le tableau de bord Django par défaut n'est plus utilisé).

## Ce qui fonctionne (10 tests automatiques)
- **Site public** : accueil animé avec message de bienvenue et cœurs bleus/blancs, Qui sommes-nous (identité, mission, équipe nationale, signes), Fédérations (fiche, équipe, coordonnateurs, sections), Activités (calendrier + plan d'action 2025–2028, rencontres, recommandations), Actualités, Galerie (+ album Google Drive, agrandissement des photos), Documentation (21 documents, recherche, filtres, consultation, téléchargement), Contact (enregistré en base).
- **Tableau de bord** `/gestion/` : vue d'ensemble avec chiffres réels, et pour chaque rubrique Ajouter / Modifier / Archiver / Restaurer (responsables, sections, documents avec fichier, actualités, photos, activités, fédérations, messages reçus).
- **Droits appliqués côté serveur** : un responsable de fédération ne gère que les responsables et sections de SA fédération ; les autres rubriques sont réservées à l'équipe nationale et aux administrateurs.

## Pas encore développé
Demandes d'adhésion et espace membre, inscriptions aux événements, notifications par e-mail, statistiques/exports PDF-Excel, documents à accès restreint.

## Installation
```
python -m venv .venv
.venv\Scripts\activate          # Windows  (Mac/Linux : source .venv/bin/activate)
pip install -r requirements.txt
set DJANGO_DEBUG=1              # PowerShell : $env:DJANGO_DEBUG="1" ; Mac/Linux : export DJANGO_DEBUG=1
python manage.py migrate
python manage.py import_federations
python manage.py import_content
python manage.py createsuperuser
python manage.py runserver
```
Site : http://127.0.0.1:8000/ — Tableau de bord : http://127.0.0.1:8000/gestion/ — Tests : `python manage.py test`

## Créer un responsable de fédération
Dans `/admin/` (réservé au superutilisateur) → Utilisateurs → Ajouter : cocher « statut équipe », rôle « Responsable de fédération », choisir sa fédération. Il se connecte ensuite sur `/comptes/login/` et arrive sur son tableau de bord.

## Production
Voir `.env.example` : `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, variables `POSTGRES_*`. Le dossier `media/` (fichiers téléversés) doit être servi par le serveur web.

## Mise à jour d'une installation existante
```
pip install -r requirements.txt
python manage.py migrate
```
La galerie accepte désormais tous les formats (photos, RAW comme .cr2, vidéos, audio, documents) ; seuls les fichiers exécutables ou scripts sont refusés. Les icônes (Bootstrap Icons) sont incluses dans `static/vendor` et fonctionnent sans connexion à un CDN.

## Assistant JEC
Bouton **Assistant JEC** dans la barre de navigation (site public et tableau de bord). Il ne répond qu'aux questions concernant la JEC.
- **Sans clé API (par défaut)** : l'assistant intégré cherche dans les contenus du site (présentation, fédérations, équipes, documents PDF/Word, activités, actualités) et répond uniquement avec eux. Il fonctionne tout de suite, gratuitement. Les questions hors sujet reçoivent un refus poli.
- **Avec une clé API Anthropic (facultatif)** : les réponses sont rédigées par une IA, toujours limitée à la JEC et appuyée sur les mêmes contenus. Définissez la variable d'environnement `ANTHROPIC_API_KEY` (voir `.env.example`). Si l'IA est indisponible, l'assistant intégré prend le relais automatiquement.
Limite : 20 questions par visiteur toutes les 10 minutes. Ce que vous ajoutez dans le tableau de bord est pris en compte au bout de 5 minutes au plus.

## Glossaire (définitions)
42 définitions tirées des documents de la JEC (JEC, JECI, CIDI, CAL, méthode Voir – Réfléchir – Agir, Révision d'Action, signes, structure…), visibles sur `/glossaire/` et utilisées en priorité par l'assistant quand on lui demande « c'est quoi… ? » ou « que signifie… ? ». Elles se gèrent dans le tableau de bord (rubrique **Définitions** : Ajouter, Modifier, Archiver). Pour les charger : `python manage.py import_content`.

## Choisir l'IA de l'assistant (facultatif)
Sans réglage, l'assistant intégré fonctionne déjà (recherche dans le site + glossaire). Pour une IA qui comprend n'importe quelle formulation, définissez UNE des deux options :
- `ANTHROPIC_API_KEY` (Anthropic, payant) ;
- `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` : tout service compatible OpenAI (par exemple Google Gemini, Groq, ou Ollama installé sur votre machine). Vérifiez les conditions et quotas gratuits actuels de chaque service.

## Application sur téléphone (bouton QR code)
Le bouton **Application** (icône QR code) en haut du site affiche un QR code : en le scannant, le téléphone ouvre le site, que l'on peut ajouter à l'écran d'accueil et utiliser comme une application (icône JEC, plein écran, page « hors connexion »). Ce n'est pas une application des boutiques Google Play / App Store : c'est une application web installable (PWA).
- Définissez `SITE_URL` (adresse publique du site) pour que le QR code pointe vers le bon endroit. Sans elle, il encode l'adresse utilisée pour consulter le site : en `localhost`, un téléphone ne peut pas l'ouvrir.
- L'installation comme application exige **HTTPS** (hors `localhost`) ; sans HTTPS, le QR code ouvre simplement le site.
- Le QR code se télécharge en PNG pour l'imprimer sur une affiche : `/application/qr.png`.
