# Test rapide des fonctionnalités Locrit

## Fonctionnalités testables immédiatement

### 1. Interface TUI
- Lancer : `./start.sh`
- Navigation avec Tab/Shift+Tab
- Raccourcis : `d` (mode sombre), `q` (quitter)

### 2. Recherche web
- Saisir : "Python programming"
- Cliquer : 🔍 Rechercher
- → Résultats DuckDuckGo avec analyse

### 3. Mémoire persistante
- Après une recherche, taper : "Python"
- Cliquer : 🧠 Mémoire
- → Retrouve l'historique des recherches

### 4. Monitoring système
- Cliquer : 💾 Statut
- → Affiche l'état de tous les services

### 5. Chat LLM (nécessite Ollama)
```bash
# Installation Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama run llama3.2

# Puis dans Locrit
# Saisir : "Bonjour, qui es-tu ?"
# Appuyer : Entrée (ou cliquer 🤖 Chat)
```

## Données générées

- `data/locrit_memory.db` : Base SQLite avec conversations
- Logs en temps réel dans l'interface
- Session IDs automatiques pour traçabilité

## Démonstration avancée

1. **Recherche + Chat** : Rechercher "IA générative" puis discuter des résultats
2. **Mémoire contextuelle** : Le locrit se souvient des conversations précédentes
3. **Workflow complet** : Recherche → Analyse → Sauvegarde → Récupération
