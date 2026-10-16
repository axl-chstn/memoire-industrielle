# Mémoire Industrielle

Une maquette pour retrouver l'expérience de maintenance dans des rapports : importer des documents, poser une question et consulter les passages qui justifient le résultat.

**Démarrage immédiat sans clé API**, avec 12 rapports fictifs issus du TD sur les pompes, moteurs et compresseurs. Le mode sans clé affiche les extraits : il ne simule pas une réponse générée par un LLM.

## Ce que fait cette version

- Import de PDF contenant du texte, de fichiers TXT et Markdown.
- Découpage en passages avec conservation du document et de la page ou du numéro de passage.
- Recherche par mots-clés BM25, filtres par équipement et respect des références explicites.
- Recherche hybride facultative avec embeddings multilingues calculés localement.
- Synthèse RAG facultative avec OpenAI et références `[S1]`, `[S2]`.
- Consultation des sources, export d'un résultat en Markdown et retrait des documents.
- Tests automatiques et jeu d'évaluation reproductible.

## Lancer sur son ordinateur

Python **3.11 ou supérieur** est nécessaire. Depuis le dossier du projet :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

Ouvrir ensuite **http://localhost:8501**. Sur Windows, remplacer la commande d'activation par `.venv\Scripts\activate`.

Sur Mac, le fichier **Lancer.command** automatise la création de l'environnement et le lancement. S'il n'est pas exécutable après téléchargement : `chmod +x Lancer.command`, puis `./Lancer.command`.

### Essayer la maquette en deux minutes

1. Les 12 rapports fictifs sont chargés au démarrage.
2. Cliquer sur « L'incident INC07 sur la pompe P01 est-il résolu ? ».
3. Ouvrir la source RAP07 : le résultat de l'intervention est **inconnu**. Ce cas ne doit pas devenir « résolu » ou « non résolu ».
4. Essayer « Quelle intervention a été réalisée sur M01_RA ? » : RAP03 documente une lubrification.
5. Essayer « Quelle panne sur P999 ? » : aucune machine connue ne doit être substituée.
6. Importer un document personnel dans la colonne de gauche ; retirer les documents fictifs dans l'onglet Documents si nécessaire.

### Activer la recherche par embeddings

```bash
python -m pip install -r requirements-semantic.txt
```

Dans « Réglages de recherche », cocher **Chercher aussi par le sens**. Le premier usage télécharge le modèle public `intfloat/multilingual-e5-small` depuis Hugging Face. Prévoir plusieurs centaines de Mo et une connexion Internet. Ensuite, les embeddings des rapports sont calculés sur la machine qui exécute l'application, sur CPU. En cas d'indisponibilité, l'application indique qu'elle utilise les mots-clés.

### Activer les réponses rédigées par un LLM

Dans « Rédiger les réponses avec une IA », saisir une **clé API OpenAI** dans le champ masqué, puis cocher **Activer les synthèses OpenAI**. Le modèle proposé est `gpt-4.1-mini` ; son accès dépend du compte API et le nom reste modifiable.

Alternative pour une configuration locale : copier `.env.example` vers `.env`, puis renseigner `OPENAI_API_KEY`. Sur un hébergement Streamlit, utiliser les secrets de l'application. Ne jamais ajouter une clé au dépôt. Un abonnement ChatGPT ne fournit pas de crédits API ; la génération utilise la facturation du compte API.

Seuls la question et les passages sélectionnés sont envoyés au fournisseur pour une synthèse. La requête fixe `store=False`, ce qui désactive le stockage de la réponse pour récupération via l'API, sans constituer une garantie d'absence de toute rétention technique par le fournisseur.

## Utiliser GitHub

GitHub héberge le **code**. Ce dépôt ne constitue pas, à lui seul, une application en ligne ; GitHub Pages n'exécute pas Streamlit/Python.

Pour lancer sans installation locale, utiliser éventuellement **Code → Codespaces → Create codespace on main**. La configuration prépare les dépendances, puis exécuter :

```bash
python -m streamlit run app.py --server.address 0.0.0.0
```

Ouvrir le port 8501 dans l'onglet Ports, en conservant sa visibilité privée. Codespaces peut consommer un quota ou des crédits selon le compte. La création et l'arrêt de cet environnement restent à la main de l'utilisateur.

## Vérifier le projet

```bash
python -m pip install -r requirements-dev.txt
ruff check .
pytest -q
python -m scripts.evaluate
# Après installation des dépendances sémantiques :
python -m scripts.evaluate --semantic
```

Les tests couvrent l'extraction PDF et sa provenance, les imports invalides, le découpage, les filtres, une référence absente, les citations inventées, l'interface et le contrat d'appel au LLM. Les tests du fournisseur utilisent un double de test : ils ne prouvent pas qu'une clé dispose de crédits ni que les synthèses réelles sont correctes.

Le corpus étant fictif et très petit, les résultats ne constituent pas une mesure de fiabilité industrielle. Voir [la fiche technique](docs/ARCHITECTURE.md), [le protocole d'essai](docs/VALIDATION.md) et [la prochaine étape](docs/ROADMAP.md).

## Données et limites

- Les rapports importés, leurs embeddings et l'historique restent dans la mémoire de la session ; ils ne sont pas enregistrés dans le dépôt. Une session interrompue peut les perdre.
- Le modèle public est mis en cache sur disque dans `.cache/`, mais aucun contenu de rapport n'est placé dans un cache global partagé.
- Limites : 10 Mo et 100 pages par fichier PDF, 30 fichiers/30 Mo par import et 50 documents par session. Pas d'OCR pour les scans.
- Les noms d'équipement sont repérés par des motifs simples. Les alias et les références inhabituelles nécessitent une adaptation.
- Le classement n'est pas une confiance statistique. Le contrôle des citations valide leurs identifiants, pas la véracité de chaque phrase.
- Pas de connexion GMAO, d'authentification propre, de stockage persistant ou de raisonnement OWL dans cette V1. Ne pas exposer cette maquette sur Internet avec des documents confidentiels sans ajouter les protections adaptées.
- Les questions sont indépendantes. L'historique affiché n'est pas envoyé au LLM ; rappeler l'équipement dans chaque question.

## Sources techniques

- [Sentence Transformers : recherche sémantique](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html)
- [Modèle E5 multilingue : consignes et limites](https://huggingface.co/intfloat/multilingual-e5-small)
- [OpenAI Docs : génération de texte](https://developers.openai.com/api/docs/guides/text)
- [OpenAI Docs : données de l'API](https://developers.openai.com/api/docs/guides/your-data)
- [Streamlit : documentation](https://docs.streamlit.io/)

Les exemples de maintenance sont des scénarios pédagogiques, pas des procédures opérationnelles.
