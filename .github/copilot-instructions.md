# Copilot Instructions pour Locrit

## Vue d'ensemble du projet

Locrit est un système de gestion de chatbots autonomes appelés "locrits". Chaque locrit possède sa propre identité, agentivité et mémoire persistante, utilisant un serveur **Ollama** pour les modèles de langage. Voir `FEATURES.md` pour la description complète des fonctionnalités.

## Architecture et structure

- **Interface utilisateur** : Layout avec sections d'input, boutons et log
- **État de développement** : Application en phase d'amorçage, architecture cible complexe (voir `FEATURES.md`)

### Architecture de données cible (Hybrid baseline)
- **SQLite** : Données canoniques (id, text, metadata, timestamps, user_id)
- **Index vectoriel** : FAISS ou pgvector pour embeddings
- **Flux de requête** : Préfiltre métadonnées (SQL) → k-NN sur embeddings → rerank → bundle vers LLM

### Modes de fonctionnement prévus
# Copilot Instructions pour Locrit

## Vue d'ensemble du projet

Locrit est un système de gestion de chatbots autonomes appelés "locrits". Chaque locrit possède sa propre identité, agentivité et mémoire persistante, utilisant un serveur **Ollama** pour les modèles de langage. Voir `FEATURES.md` pour la description complète des fonctionnalités.

## Architecture et structure

- **Interface utilisateur** : Layout avec sections d'input, boutons et log
- **État de développement** : Application en phase d'amorçage, architecture cible complexe (voir `FEATURES.md`)

### Architecture de données cible (Hybrid baseline)
- **SQLite** : Données canoniques (id, text, metadata, timestamps, user_id)
- **Index vectoriel** : FAISS ou pgvector pour embeddings
- **Flux de requête** : Préfiltre métadonnées (SQL) → k-NN sur embeddings → rerank → bundle vers LLM

### Modes de fonctionnement prévus
1. **Chat utilisateur** : Interface directe (implémentation actuelle)
2. **Mode serveur** : API pour communication avec autres locrits/LLMs
3. **Mode client** : Connexion vers autres locrits/LLMs
4. **Recherche internet** : Intégration DuckDuckGo autonome
5. **Agentivité** : Actions multi-étapes, navigation web, communication inter-locrits


## Dépendances et intégrations prévues

Les dépendances dans `requirements.txt` révèlent l'architecture cible complexe :
- **ollama** : Client LLM local pour chaque locrit (TODO dans `analyze_btn`)
- **duckduckgo-search** : Recherche web autonome (TODO dans `search_btn`) 
- **beautifulsoup4/lxml** : Parsing HTML pour navigation web agentive
- **sqlite-utils** : Base de données locale + métadonnées (TODO dans `save_btn`)
- **FAISS/pgvector** : Index vectoriel pour mémoire (à ajouter)

### Configuration Ollama requise
- Interface pour configurer l'adresse serveur Ollama (localhost:port par défaut)
- Indicateurs de statut : LLM, mémoire, outils d'agentivité, connexion serveur
- Gestion des connexions multiples pour communication inter-locrits

## Conventions de développement

### Messages utilisateur
- **Emojis systématiques** : 🔍 pour recherche, 🤖 pour IA, 💾 pour sauvegarde, ❌ pour erreurs
- **Messages bilingues** : Interface en français, code et commentaires en français

### Pattern d'extension
Pour ajouter de nouvelles fonctionnalités :
1. Ajouter le bouton dans `compose()` avec un ID unique
2. Étendre `on_button_pressed()` avec un nouveau `elif event.button.id == "nouveau_btn"`
3. Utiliser `log.write_line()` pour le feedback utilisateur

### État de l'application
- **Log central** : Widget `Log` avec ID `results_log` sert de console de sortie
- **Focus management** : `search_input` reçoit le focus au démarrage
- **Raccourcis clavier** : `d` pour dark mode, `q` pour quitter (définis dans `BINDINGS`)

## Commandes de développement

```bash
# Lancer l'application
python main.py

# L'environnement virtuel est pré-configuré dans .venv/
# Pas besoin d'activation manuelle si configuré correctement
```

## Points d'extension immédiats

Les TODOs dans `src/app.py` indiquent les prochaines étapes vers l'architecture complète :
- `search_btn` : Intégrer `duckduckgo-search` pour recherche autonome
- `analyze_btn` : Intégrer client `ollama` avec gestion identité du locrit
- `save_btn` : Implémenter mémoire hybride (SQLite + embeddings)

### Fonctionnalités avancées à développer
- **Mode serveur** : API REST/WebSocket pour communication inter-locrits
- **Tunneling** : Intégration localhost.run/pinggy.io pour accès distant
- **Agentivité** : Système de planification et exécution d'actions multi-étapes
- **Configuration** : Interface pour paramètres Ollama et indicateurs de statut

## Vue d'ensemble du projet

Locrit est un système de gestion de chatbots autonomes appelés "locrits". Chaque locrit possède sa propre identité, agentivité et mémoire persistante, utilisant un serveur **Ollama** pour les modèles de langage. Voir `FEATURES.md` pour la description complète des fonctionnalités.

## Maintien de la documentation sur les fonctionnalités clés de l’application

Pour assurer la pérennité et la clarté de l'application, il est essentiel de maintenir une documentation à jour sur ses fonctionnalités clés. Cela inclut :

- Descriptions détaillées des fonctionnalités
- Instructions d'utilisation pour les utilisateurs finaux
- Notes de version pour suivre les changements et améliorations

Notes les dans le FEATURES.md. 

--- NOT DONE ---

## Patterns spécifiques à Textual

### CSS intégré
- CSS défini comme string dans la classe avec unités spéciales (`1fr` pour flex)
- Classes CSS appliquées via `classes="nom-classe"` sur les conteneurs

## Dépendances et intégrations prévues

Les dépendances dans `requirements.txt` révèlent l'architecture cible :

## Conventions de développement
--- NOT DONE ---