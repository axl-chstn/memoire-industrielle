# Mémoire industrielle

Ce dépôt contient la maquette du projet Mémoire industrielle. L'objectif est de retrouver ce qui a déjà été observé et tenté sur un équipement à partir des rapports de maintenance.

Par exemple, lorsqu'une pompe vibre, on peut consulter les incidents précédents, voir les interventions réalisées et vérifier si elles ont résolu le problème. Chaque réponse renvoie aux passages des rapports utilisés.

L'application fonctionne en local avec Python et Streamlit. La recherche et le modèle de langage tournent sur l'ordinateur, sans clé API ni frais d'API.

## Ce que contient la maquette

Un atelier fictif sert de terrain d'essai : 10 équipements, 30 rapports et 22 incidents. Certains incidents ont plusieurs rapports de suivi, ce qui permet de distinguer une première intervention sans succès d'une résolution plus tardive.

Les écrans permettent de consulter les équipements, suivre les incidents, chercher des cas similaires et poser des questions aux rapports. La bibliothèque donne accès aux textes et aux informations extraites, que l'on peut corriger et valider.

L'espace **Mes documents** permet d'ajouter ses propres rapports, séparément du scénario fictif. Les données de démonstration ne sont pas des données industrielles réelles.

## Installation et lancement

Sur Mac, utiliser Python 3.12 et prévoir plusieurs Go de disque disponibles. Le modèle choisi, `qwen3:4b-instruct`, occupe environ 2,5 Go. La maquette a été testée sur un Mac Apple Silicon avec 8 Go de mémoire.

Depuis le dossier du projet :

```bash
chmod +x Lancer.command
./Lancer.command
```

Le premier lancement télécharge les dépendances, Ollama et le modèle. Il faut donc une connexion Internet et un peu de temps. Les téléchargements sont conservés pour les lancements suivants.

L'application est ensuite accessible sur [http://127.0.0.1:8501](http://127.0.0.1:8501). Cette adresse correspond à l'application qui tourne sur l'ordinateur ; GitHub héberge uniquement le code.

Pour lancer les étapes manuellement :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m scripts.local_runtime
python -m streamlit run app.py --server.address 127.0.0.1
```

Sur Windows, la commande d'activation est `.venv\Scripts\activate`. Sur Windows et Linux, installer d'abord [Ollama](https://ollama.com/download). Le téléchargement automatique du moteur est prévu pour macOS.

Si le modèle n'est pas disponible, la recherche et la consultation des extraits restent utilisables.

## Quelques essais

Dans **Incidents**, ouvrir **INC114** : une lubrification n'a pas résolu les vibrations, puis un réalignement a permis de résoudre le problème. Les deux étapes doivent rester visibles.

Dans **Questions**, essayer :

- « L'incident INC104 est-il résolu ? »
- « Qu'a-t-on essayé pour les vibrations sur C03 ? »
- « Quels rapports parlent de la pompe d'alimentation ? »

Pour comparer des cas, partir d'**INC116** dans **Cas similaires**, puis sélectionner **Vibration** et **Roulement**. Les résultats indiquent les points communs entre incidents. Cela ne suffit pas à conclure qu'ils ont la même cause.

## Ajouter ses rapports

Dans **Mes documents**, importer des PDF contenant du texte, des fichiers TXT ou Markdown. Les PDF scannés nécessitent un OCR préalable, qui n'est pas inclus.

L'application repère les identifiants et les rubriques explicites, comme l'incident, l'équipement, la date, les symptômes, le diagnostic, l'intervention et le résultat. Un rapport rédigé librement peut demander davantage de corrections manuelles.

Les fiches importées sont à vérifier dans **Documents** avant d'apparaître dans les vues d'incidents. Pour corriger une information, fournir la valeur et l'extrait du rapport qui la justifie, puis valider la fiche. Une nouvelle correction annule la validation précédente.

Les limites actuelles sont de 10 Mo et 100 pages par PDF, 30 fichiers et 30 Mo par import, puis 100 documents et 100 Mo sauvegardés par espace.

## Sauvegarde et données locales

Les textes extraits, les corrections et les validations sont enregistrés automatiquement dans `data/private/espaces.sqlite3`. Ils restent disponibles après un redémarrage. Ce dossier est exclu de Git et les rapports ne sont pas envoyés sur GitHub. Les PDF originaux sont à conserver séparément ; l'historique des questions reste dans la session.

Le menu **Sauvegarde de cet espace**, dans la colonne de gauche, permet de télécharger un export JSON et de le restaurer sur une autre installation. La restauration ajoute les documents absents et conserve ceux qui sont déjà présents, avec leurs fiches. Les fiches ajoutées doivent être vérifiées à nouveau.

Les exports contiennent le texte des rapports. Le stockage local n'est pas chiffré par l'application et les espaces ne sont pas conçus pour séparer plusieurs utilisateurs.

## Recherche et modèle local

Les rapports sont découpés en passages en conservant leur document et leur page d'origine. La recherche utilise BM25 pour retrouver les termes et les références demandés. Elle peut être complétée par des embeddings multilingues calculés localement :

```bash
python -m pip install -r requirements-semantic.txt
```

Activer ensuite **Chercher aussi par le sens** dans les réglages. Le premier usage télécharge le modèle `intfloat/multilingual-e5-small` depuis Hugging Face. Cette option concerne la recherche dans **Questions**.

Les réponses sur les dates, les interventions, les diagnostics et les résultats sont composées à partir des fiches vérifiées. Un rapport sans date reste à part de la chronologie ; une intervention non renseignée reste une information inconnue.

Ollama tourne sur `127.0.0.1:11435`, avec les fonctions cloud désactivées. Pour les questions libres, il sélectionne des passages que l'application recopie sans reformulation. Le modèle ne rédige plus de conclusions libres. Cela limite les affirmations ajoutées, mais la pertinence des passages choisis et leur contexte restent à vérifier. Si la sélection est inexploitable, les fiches et les sources restent accessibles.

Les modèles sont conservés dans `.cache/` et le moteur dans `.local/`, tous deux exclus de Git. Les détails de fonctionnement sont décrits dans [l'architecture](docs/ARCHITECTURE.md).

## Tests

```bash
python -m pip install -r requirements-dev.txt
ruff check .
pytest -q
python -m scripts.evaluate
python -m scripts.evaluate_workshop
python -m scripts.evaluate_rives
```

Après installation des embeddings, les deux scripts d'évaluation acceptent l'option `--semantic`. Pour tester le modèle de langage installé :

```bash
python -m scripts.validate_local
python -m scripts.evaluate_rives --local
```

Les vingt questions de l’atelier des Rives sont conservées comme tests de régression après correction des erreurs observées. Elles ne constituent donc plus un jeu d’essai indépendant.

Les résultats obtenus et la portée des essais sont détaillés dans [les vérifications](docs/VERIFICATION.md). Les 12 fiches historiques du TD sont conservées pour vérifier que les évolutions ne cassent pas les premiers exemples.

## Ce qu'il reste à faire

La maquette permet de tester le parcours sur des exemples préparés. Il reste à l'évaluer sur des rapports indépendants et à la faire essayer par des personnes du métier. Le modèle peut sélectionner un passage peu pertinent, et une fiche vérifiée peut encore contenir une erreur humaine. Les références permettent de revenir aux rapports ; elles ne suffisent pas à établir toutes les conclusions.

Les concepts de l'ontologie servent à organiser les équipements, composants, incidents et interventions. Le raisonneur OWL n'est pas intégré. La maquette ne comporte pas non plus de connexion à une GMAO ni d'authentification pour un usage partagé.

La prochaine étape prévue est de réunir 5 à 10 rapports autorisés et anonymisés, puis de préparer des questions avec les réponses attendues. Voir le [protocole d'essai](docs/VALIDATION.md) et la [suite du projet](docs/ROADMAP.md).
