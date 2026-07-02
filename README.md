
# CESIZen

Application web de gestion du stress et de bien-être mental, développée dans le cadre du titre **Concepteur Développeur d'Applications (CDA)** — CESI École d'ingénieurs.

## Qualité du code

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Norlik13_CEZIZen&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Norlik13_CEZIZen)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=Norlik13_CEZIZen&metric=coverage)](https://sonarcloud.io/summary/new_code?id=Norlik13_CEZIZen)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=Norlik13_CEZIZen&metric=bugs)](https://sonarcloud.io/summary/new_code?id=Norlik13_CEZIZen)

## Stratégie Git (GitFlow simplifié)

### Branches

| Branche | Rôle |
|---------|------|
| `master` | Branche principale — code stable, déployé en production |
| `develop` | Branche d'intégration — nouvelles fonctionnalités en cours |
| `feature/*` | Branches de développement — une par fonctionnalité |
| `fix/*` | Branches de corrections de bugs |

### Workflow

```
master ──────────────────────────────────────────► production
  │
  └── develop ──────────────────────────────────► intégration
        │
        ├── feature/nom-feature ──► PR vers master
        └── fix/nom-fix         ──► PR vers master
```

1. Créer une branche `feature/nom` ou `fix/nom` depuis `master`
2. Développer et pousser les commits
3. Ouvrir une **Pull Request** vers `master`
4. La CI doit passer (tests + Quality Gate SonarCloud verte)
5. Au moins 1 approbation requise
6. Merge via PR uniquement — **push direct interdit sur `master`**

### Protection de la branche `master`

- Push direct bloqué
- PR obligatoire avec minimum 1 approbation
- Les checks CI (tests + SonarCloud Quality Gate) doivent être verts avant le merge

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Framework | Django 6.0.3 (Python 3.13) |
| Base de données (dev) | SQLite |
| Base de données (prod) | MariaDB |
| Serveur WSGI | Gunicorn |
| Reverse proxy | Nginx |
| Conteneurisation | Docker + Docker Compose |
| CI/CD | GitHub Actions (runner local) |
| Qualité du code | SonarCloud |

## Pipeline CI/CD

Le pipeline tourne sur un **runner local** (self-hosted) et exécute à chaque `push` et `pull_request` sur `master` :

| Étape | Commande | Équivalent |
|-------|----------|------------|
| Installation des dépendances | `pip install -r requirements.txt` | `dotnet restore` |
| Vérification du projet | `python manage.py check` | `dotnet build` |
| Tests avec couverture | `coverage run manage.py test` | `dotnet test` |
| Analyse SonarCloud | `sonarcloud-github-action` | — |

Le job Docker (build + push GHCR) tourne lui sur un runner GitHub-hébergé.

## Installation locale (sans Docker)

```bash
git clone https://github.com/Norlik13/CEZI_zen
cd CEZI_zen
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_emotions
python manage.py seed_legal_pages
python manage.py createsuperuser
python manage.py runserver
```

Application disponible sur **http://localhost:8000**

## Démarrage avec Docker (recommandé)

```bash
# Développement
cp .env.dev.example .env.dev
docker compose up --build

# Production
cp .env.prod.example .env.prod
# Éditer .env.prod avec les vraies valeurs
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## Tests

```bash
python manage.py test --verbosity=2
# 96 tests — unitaires, fonctionnels et intégration
```

## Structure du projet

```
CEZIZen/
├── accounts/          # Gestion des utilisateurs et authentification
├── infos/             # Pages d'information et articles
├── emotions/          # Tracker d'émotions
├── templates/         # Templates HTML
├── .github/
│   ├── workflows/ci.yml           # Pipeline CI/CD GitHub Actions
│   ├── ISSUE_TEMPLATE/            # Templates de tickets
│   └── pull_request_template.md
├── sonar-project.properties       # Configuration SonarCloud
├── nginx/nginx.conf               # Configuration reverse proxy
├── Dockerfile
├── docker-compose.yml             # Dev local
├── docker-compose.prod.yml        # Production
├── .env                           # Variables dev (commité, sans secrets)
└── .env.prod.example              # Modèle production (ne pas commiter .env.prod)
```