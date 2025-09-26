#!/bin/bash
# Script de lancement de Locrit

echo "🚀 Lancement de Locrit..."

# Vérifier si l'environnement virtuel existe
if [ ! -d ".venv" ]; then
    echo "❌ Environnement virtuel non trouvé. Veuillez d'abord installer le projet."
    exit 1
fi

# Lancer l'application avec l'environnement virtuel
./.venv/bin/python main.py
