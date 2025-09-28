
# Contexte du projet. 

Les Locrits sont des personnages qui sont animés par des LLMs.
Ces personnages sont «locaux» c'est à dire sur une machine. 

Fonctionnalité d'un Locrit:  
* Personnalité propre (prompt initial)
* Mémoire propre avec des avis (via graphe à implémenter) et souvenirs (mémoire vectorielle)

Comment un Locrit «vit» : 
* L'utilisateur local peut lui parler directement via cette application. 
* Il peut être exposé en ligne (via un reverse proxy tunnel par ex) pour permettre à d'autres personnes de lui parler. 
* Il peut aller parler à un autre Locrit sur instruction de l'utilisateur ou de manière autonome. 
* Il peut aller sur un «chat» dédié au Locrits de durée éphémère. 

Les Locrits sont repertoriés en ligne : 
* Grâce au FireStore pour stocker les informations sur les Locrits. 
* Pour savoir comment trouver d'autres locrits et leurs parler. 
* Le réseau Locrit est sur un autre dépôt / code. 

Ce dépôt / code est pour les locrits locaux. 

L'interface est en React, et doit être sympathique et enfantine. 
Les locrits sont un peu des «enfants» ou «petits animaux» IA et 
l'UX - UI doit reflèter ça. 

## Avancement. 

Dans les premières étapes on est focus sur : 
* l'implémentation de l'UI en React. 
* Leur parler avec un prompt : L0. 
* Leur parler avec un côté agentique : L1. 
* Leur parler avec une mémoire de graphe : L2. 
* Leur parler avec une mémoire vectorielle : L3.  
* La création du serveur Locrit qui permet de leur donnée vie (API - UI)

# Code instructions : 

For Python use the venv in  .venv directory.

Do not write code in the documentations. 

The python UI using `textual` is deprecated. Do not 
use Textual and delete the old files when finding them. 

When the code is too long (> 800 lignes) split it in modules or sub-components. 

Trust the frameworks. Avoid writing yourself CSS code when the components should
work correctly using shadcn. Write tailwindcss instead of pure CSS when possible. 

Use BrowserMCP to debug as much as possible.

In the UI, allow auto-saves for each field or save buttons 
beside them when more important fields. Do not put save buttons
at the bottom of the pages.

We can always chat with our local locrits .