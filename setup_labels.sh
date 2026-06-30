#!/bin/bash
# setup_labels.sh — Crée les labels GitHub Issues pour CESIZen
# Usage : bash setup_labels.sh Norlik13/CEZI_zen
# Prérequis : gh auth login

REPO=${1:-"Norlik13/CEZI_zen"}
echo "→ Configuration des labels pour $REPO"

create_label() {
  gh label create "$1" --color "$2" --description "$3" --repo "$REPO" --force
  echo "  ✓ $1"
}

echo "── Type ───────────────────────────────────────────────────────"
create_label "bug"                "d73a4a" "Anomalie fonctionnelle à corriger"
create_label "enhancement"        "a2eeef" "Demande d'évolution ou nouvelle fonctionnalité"
create_label "security"           "e4e669" "Vulnérabilité ou incident de sécurité"
create_label "documentation"      "0075ca" "Amélioration de la documentation"
create_label "chore"              "e4e4e4" "Tâche technique (dépendances, refacto)"

echo "── Sévérité ───────────────────────────────────────────────────"
create_label "bloquant critique"  "b60205" "SLA : 1h diagnostic / 3h correction"
create_label "bloquant fort"      "e11d48" "SLA : 2h diagnostic / 6h correction"
create_label "majeur"             "f97316" "SLA : 7h diagnostic / 16h correction"
create_label "mineur"             "fef08a" "SLA : 1j diagnostic / 40h correction"

echo "── Statut ─────────────────────────────────────────────────────"
create_label "à qualifier"        "ededed" "Nouveau ticket, sévérité non évaluée"
create_label "à analyser"         "d4c5f9" "En attente d'analyse technique"
create_label "en cours"           "0052cc" "Développement en cours"
create_label "en review"          "5319e7" "Pull Request ouverte"
create_label "en staging"         "1d76db" "Déployé en staging, en attente de validation"
create_label "en attente client"  "fbca04" "En attente d'une réponse client"
create_label "wontfix"            "ffffff" "Ne sera pas corrigé"
create_label "doublon"            "cfd3d7" "Ticket déjà ouvert ailleurs"
create_label "confidentiel"       "b60205" "Ne pas divulguer (sécurité / RGPD)"

echo "── Module ─────────────────────────────────────────────────────"
create_label "module: comptes"    "c5def5" "App accounts"
create_label "module: infos"      "bfd4f2" "App infos"
create_label "module: tracker"    "baffc9" "App emotions"
create_label "module: back-office" "ffd1a0" "Interface d'administration"
create_label "module: infra"      "f9d0c4" "Docker, CI/CD, Nginx"

echo ""
echo "✅ Labels configurés sur $REPO"
