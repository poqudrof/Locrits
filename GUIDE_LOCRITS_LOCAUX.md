# 🏠 Guide d'utilisation - Mes Locrits Locaux

## 📋 Vue d'ensemble
L'écran "Mes Locrits Locaux" affiche maintenant tous vos Locrits stockés dans `config.yaml` et gère leur synchronisation avec Firestore.

## 🚀 Comment accéder à l'écran
1. Lancez l'application : `source .venv/bin/activate && python main.py`
2. Connectez-vous (Anonyme ou avec email/mot de passe)
3. Sur l'écran d'accueil, cliquez sur "📋 Mes Locrits Locaux"

## 📊 Fonctionnalités implémentées

### 🔍 Affichage des Locrits
- **4 Locrits détectés** dans votre config.yaml :
  - 🤖 **Bob Technique** - Expert en programmation (Actif)
  - 🤖 **Locrit root** - Le premier Locrit
  - 🤖 **Marie Recherche** - Spécialisée en recherche
  - 🤖 **Pixie Assistant** - Assistant personnel (Actif)

### 📝 Informations affichées
Pour chaque Locrit :
- 🟢/🔴 **Statut** (actif/inactif)
- 📝 **Description**
- 📅 **Date de création**
- 🤖 **Modèle Ollama utilisé**
- 🌐 **Adresse publique**

### 🔄 Synchronisation Firestore
- **Zone de logs** en temps réel
- **Synchronisation automatique** au chargement
- **Bouton "🔄 Synchroniser"** pour synchronisation manuelle
- **Vérification** des Locrits manquants sur Firestore
- **Upload automatique** des nouveaux Locrits

### ⚙️ Actions disponibles
- **▶️ Démarrer** / **⏹️ Arrêter** un Locrit
- **💬 Chat** avec un Locrit actif
- **⚙️ Configurer** un Locrit
- **🗑️ Supprimer** un Locrit
- **➕ Créer Nouveau** Locrit

## 🔥 Configuration Firebase requise

Pour utiliser la synchronisation Firestore, configurez ces paramètres dans `config.yaml` :

```yaml
firebase:
  api_key: 'votre_api_key'
  auth_domain: 'votre_projet.firebaseapp.com'
  database_url: 'https://votre_projet.firebaseio.com'
  project_id: 'votre_projet_id'
  storage_bucket: 'votre_projet.appspot.com'
```

## 📱 Interface utilisateur

```
🏠 Mes Locrits Locaux
┌─────────────────────────────────────────┐
│ 🔍 Vérification synchronisation...      │
│ 📋 4 Locrit(s) trouvé(s) en local      │
│ ⚠️ Configuration Firebase requise       │
│ 💡 Configurez Firebase dans config.yaml │
└─────────────────────────────────────────┘

🤖 Bob Technique               ▶️ 💬 ⚙️ 🗑️
📝 Expert en programmation
📅 2025-09-13 | 🤖 codellama | 🌐 bob.dev.local

🤖 Locrit root                ▶️ ⚙️ 🗑️  
📝 Le premier Locrit
📅 2025-09-14 | 🤖 llama3.2 | 🌐 (aucune)

[➕ Créer Nouveau] [🔄 Synchroniser] [🔙 Retour]
```

## 🔧 Messages d'état possibles

### ✅ Succès
- `✅ Synchronisation terminée avec succès`
- `📤 Uploadés: Bob Technique, Marie Recherche`
- `📥 Téléchargés: Nouveau Locrit`

### ⚠️ Avertissements  
- `⚠️ Configuration Firebase requise`
- `⚠️ Authentification requise pour Firestore`
- `ℹ️ Aucun Locrit local à synchroniser`

### ❌ Erreurs
- `❌ Erreur de synchronisation: [détails]`
- `❌ Upload Bob Technique: Connexion échouée`

## 💡 Conseils d'utilisation

1. **Premier usage** : Testez d'abord en local sans Firebase
2. **Configuration Firebase** : Ajoutez vos clés pour la sync
3. **Synchronisation** : Les Locrits sont uploadés automatiquement
4. **Gestion locale** : Toutes les actions fonctionnent sans Firebase

## 🐛 Résolution de problèmes

- **Locrits non visibles** : Vérifiez `config.yaml` 
- **Sync échoue** : Configurez Firebase dans `config.yaml`
- **Erreur auth** : Reconnectez-vous dans l'application
- **Interface bloquée** : Redémarrez avec `Ctrl+C` puis relancez

L'écran est maintenant prêt à utiliser ! 🎉
