#!/bin/bash
# Script de démarrage de l'interface web Locrit

echo "🌐 Démarrage de l'interface web Locrit..."

# Vérifier que l'environnement virtuel existe
if [ ! -d ".venv" ]; then
    echo "❌ Environnement virtuel non trouvé. Veuillez l'installer d'abord."
    exit 1
fi

# Activer l'environnement virtuel
source .venv/bin/activate

# Installer Flask si nécessaire
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Installation de Flask..."
    pip install flask>=2.3.0 requests>=2.28.0
fi

# Vérifier que les fichiers nécessaires existent
if [ ! -f "web_app.py" ]; then
    echo "❌ Fichier web_app.py non trouvé."
    exit 1
fi

if [ ! -f "config.yaml" ]; then
    echo "⚠️ Fichier config.yaml non trouvé. Un fichier par défaut sera créé."
fi

# Démarrer l'interface web
echo "🚀 Lancement de l'interface web sur http://127.0.0.1:5000"
echo "📝 Utilisez Ctrl+C pour arrêter le serveur"
echo ""

python web_app.py