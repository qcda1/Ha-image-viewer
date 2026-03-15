#!/bin/bash
# deploy.sh — Déploiement de ha-image-viewer depuis GitHub vers Home Assistant
# Usage : ./deploy.sh [--rebuild] [--no-restart]
#   --rebuild    : Force la reconstruction du conteneur Docker (nécessaire si Dockerfile ou image-viewer.py changé)
#   --no-restart : Pull uniquement, sans redémarrer ni reconstruire

# Afin d'éviter les erreurs de changements locaux en faisant les chmod +x des scripts .sh
# on peut désactiver le suivi des permissions dans git sur HA avec la commande:
# git config core.fileMode false


set -e

ADDON_DIR=~/addons/dc_apps/image_viewer
ADDON_SLUG=local_dc_image_viewer
BRANCH=main

echo "======================================"
echo "  Déploiement ha-image-viewer"
echo "======================================"

# Vérifier que le répertoire existe
if [ ! -d "$ADDON_DIR" ]; then
    echo "❌ Répertoire $ADDON_DIR introuvable"
    exit 1
fi

cd "$ADDON_DIR"

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
git fetch origin
git reset --hard origin/"$BRANCH"
chmod +x deploy.sh run.sh

echo ""
echo "📋 Derniers commits déployés :"
git --no-pager log --oneline -5

# Rebuild ou restart selon l'option
if [ "$1" == "--no-restart" ]; then
    echo ""
    echo "⏭️  Redémarrage ignoré (--no-restart)"

elif [ "$1" == "--rebuild" ]; then
    echo ""
    echo "🔨 Reconstruction du conteneur Docker..."
    ha addons rebuild "$ADDON_SLUG"
    echo "✅ Reconstruction terminée"
    echo ""
    echo "🔄 Démarrage de l'addon $ADDON_SLUG..."
    ha addons start "$ADDON_SLUG"
    echo "✅ Addon démarré"

else
    echo ""
    echo "🔄 Redémarrage de l'addon $ADDON_SLUG..."
    ha addons restart "$ADDON_SLUG"
    echo "✅ Addon redémarré"
    echo ""
    echo "💡 Si les changements ne sont pas visibles, relancez avec : ./deploy.sh --rebuild"
fi

echo ""
echo "✅ Déploiement terminé !"
echo "======================================"