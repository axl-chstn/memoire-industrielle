# Mémoire Industrielle

Une maquette RAG pour retrouver l'expérience de maintenance dans des rapports : importer des documents, poser une question et consulter les passages qui justifient la réponse.

**Aucune clé API, aucun abonnement au modèle et aucun frais d'API.** La recherche et la rédaction des réponses s'exécutent sur la machine qui lance l'application. Le branchement OpenAI de la première version a été retiré ; une ancienne clé configurée dans l'environnement est ignorée.

## Démarrage sur Mac

Python **3.11 ou supérieur** est nécessaire, avec une version disposant des filtres de sécurité de `tarfile` pour le téléchargement automatique (Python 3.12 convient). Sur un Mac Apple Silicon avec 8 Go de mémoire, le modèle choisi est `qwen3:4b-instruct`, environ 2,5 Go sur disque. Le premier lancement nécessite Internet pour télécharger Ollama et les poids publics. Ensuite, la génération fonctionne sans service distant. Prévoir plusieurs Go de disque disponibles ; la vitesse dépend de la machine.

Depuis le dossier du projet :

```bash
chmod +x Lancer.command
./Lancer.command
```

Le lanceur prépare l'environnement Python, télécharge Ollama si nécessaire, démarre le moteur en mode local et prépare le modèle. Il ouvre ensuite l'application sur **http://127.0.0.1:8501**. Les téléchargements initiaux sont réutilisés lors des lancements suivants.

Si le modèle ne peut pas être préparé, la recherche et la lecture des extraits restent disponibles. Il n'existe aucun basculement vers un service payant.

### Lancement manuel

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m scripts.local_runtime
python -m streamlit run app.py --server.address 127.0.0.1
```

Sur Windows, l'activation est `.venv\Scripts\activate`. Sur Windows et Linux, installer d'abord [Ollama depuis son site officiel](https://ollama.com/download) ; le téléchargement automatique du moteur concerne macOS.

## Essayer en deux minutes

Les **12 rapports fictifs du TD** sur les pompes, moteurs et compresseurs sont chargés au démarrage.

1. Vérifier le message **Modèle local prêt · aucun frais d'API** dans la colonne de gauche.
2. Laisser **Rédiger les réponses sur cet ordinateur** activé.
3. Demander : « L'incident INC07 sur la pompe P01 est-il résolu ? ».
4. Ouvrir RAP07 pour vérifier que la réponse conserve un **résultat inconnu**, sans le transformer en résolution ou en non-résolution.
5. Essayer « Quelle panne sur P999 ? » : aucune machine connue ne doit être substituée.
6. Importer ses documents dans la colonne de gauche et retirer les exemples dans l'onglet Documents si nécessaire.

La première génération peut être plus lente pendant le chargement du modèle. Décoche la rédaction locale pour afficher uniquement les extraits. Une synthèse sans références valides est remplacée par les sources.

## Fonctionnalités

- Import de PDF contenant du texte, TXT et Markdown.
- Découpage avec conservation du document, de la page et du numéro de passage.
- Recherche BM25, filtres par équipement et respect des références explicites.
- Recherche hybride facultative avec embeddings multilingues calculés localement.
- Réponses rédigées par le modèle local avec citations `[S1]`, `[S2]`.
- Consultation des sources, export Markdown et retrait des documents.
- Tests automatiques et jeu d'évaluation reproductible.

### Recherche par embeddings

```bash
python -m pip install -r requirements-semantic.txt
```

Cocher **Chercher aussi par le sens** dans les réglages de recherche. Le premier usage télécharge le modèle public `intfloat/multilingual-e5-small` depuis Hugging Face. Les rapports sont encodés sur la machine qui exécute l'application. Cette recherche n'utilise pas d'API facturée.

## Fonctionnement local et données

- Ollama écoute uniquement sur `127.0.0.1:11435`, un port réservé à cette maquette.
- Le lanceur définit `OLLAMA_NO_CLOUD=1` et ne demande ni connexion à un compte ni clé.
- L'application utilise une adresse locale fixe, ne suit aucune redirection et n'utilise pas les proxys HTTP pour les questions.
- Le modèle est fixé à `qwen3:4b-instruct`. Avant chaque génération, ses métadonnées doivent décrire des poids GGUF locaux ; un modèle distant est refusé.
- Les documents et l'historique restent en mémoire dans la session. Ils ne sont pas envoyés sur GitHub et peuvent être perdus à la fermeture de la session.
- `.local/` contient le moteur et `.cache/` les modèles publics et les journaux techniques du moteur. Ils sont exclus de Git. L'installation d'Ollama peut aussi créer ses fichiers de fonctionnement dans `~/.ollama`.
- Le modèle peut rester chargé cinq minutes après une réponse, puis libérer sa mémoire. Le serveur local peut rester en arrière-plan pour les prochains essais.

Le coût de fonctionnement correspond aux ressources habituelles de l'ordinateur et aux téléchargements initiaux ; aucun fournisseur ne facture les questions. Un hébergement externe éventuel aurait ses propres coûts : la version documentée ici se lance sur son ordinateur.

## Vérifications

```bash
python -m pip install -r requirements-dev.txt
ruff check .
pytest -q
python -m scripts.evaluate
# Après installation du modèle d'embeddings :
python -m scripts.evaluate --semantic
# Après préparation du LLM local :
python -m scripts.validate_local
```

Voir [les vérifications réalisées](docs/VERIFICATION.md), [la fiche technique](docs/ARCHITECTURE.md), [le protocole d'essai](docs/VALIDATION.md) et [la prochaine étape](docs/ROADMAP.md).

## Limites

Cette maquette ne constitue pas une validation industrielle. Un modèle local peut se tromper et les citations doivent être relues. Le contrôle vérifie les identifiants des sources, pas l'appui de chaque affirmation.

Limites : 10 Mo et 100 pages par PDF, 30 fichiers/30 Mo par import, 50 documents par session. Pas d'OCR, de GMAO, de stockage persistant, d'authentification propre ni de raisonnement OWL. Les références sont repérées par des motifs simples. Les questions sont indépendantes : rappeler l'équipement à chaque fois.

GitHub héberge le code et ne fait pas tourner cette application Python. En cas de déploiement partagé, ajouter les protections et la séparation des espaces appropriées.

## Sources techniques

- [Ollama : génération locale](https://docs.ollama.com/api/chat)
- [Ollama : désactivation des fonctions cloud](https://docs.ollama.com/faq#how-do-i-disable-ollamas-cloud-features)
- [Qwen3 4B Instruct : modèle choisi](https://ollama.com/library/qwen3:4b-instruct)
- [Sentence Transformers : recherche sémantique](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html)
- [Modèle E5 multilingue](https://huggingface.co/intfloat/multilingual-e5-small)
- [Streamlit](https://docs.streamlit.io/)

Les exemples de maintenance sont des scénarios pédagogiques, pas des procédures opérationnelles.
