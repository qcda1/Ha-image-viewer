#!/bin/bash
# deploy.sh — Déploiement de ha-image-viewer depuis GitHub vers Home Assistant
# Usage : ./deploy.sh [--no-restart]

set -e

APPS_DIR=~/addons/dc_apps/image_viewer
APPS_SLUG=local_dc_image_viewer
BRANCH=main

echo "======================================"
echo "  Déploiement ha-image-viewer"
echo "======================================"

# Vérifier que le répertoire existe
if [ ! -d "$APPS_DIR" ]; then
    echo "❌ Répertoire $APPS_DIR introuvable"
    exit 1
fi

cd "$APPS_DIR"

# Vérifier que c'est bien un repo git
if [ ! -d ".git" ]; then
    echo "⚠️  Pas de repo git trouvé — initialisation..."
    git init
    git remote add origin $(git -C ~/devel/ha-image-viewer remote get-url origin 2>/dev/null || echo "")
    if [ -z "$(git remote get-url origin 2>/dev/null)" ]; then
        echo "❌ Impossible de trouver l'URL du remote. Configurez-la manuellement :"
        echo "   git remote add origin https://github.com/qcda1/ha-image-viewer.git"
        exit 1
    fi
fi

# Pull depuis GitHub
echo ""
echo "📥 Récupération des dernières modifications depuis GitHub ($BRANCH)..."
git pull origin "$BRANCH"

echo ""
echo "📋 Derniers commits déployés :"
git log --oneline -5

# Redémarrer l'application sauf si --no-restart
if [ "$1" != "--no-restart" ]; then
    echo ""
    echo "🔄 Redémarrage de l'application $APPS_SLUG..."
    ha apps restart "$APPS_SLUG"
    echo "✅ Application redémarré"
else
    echo ""
    echo "⏭️  Redémarrage ignoré (--no-restart)"
fi

echo ""
echo "✅ Déploiement terminé !"
echo "======================================"
