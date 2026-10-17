# Mémoire Industrielle · V2 Atelier

Une maquette RAG pour retrouver l'expérience de maintenance dans des rapports : importer des documents, poser une question et consulter les passages qui justifient la réponse.

La V2 propose un atelier fictif complet : **10 équipements, 30 rapports et 22 incidents**, dont plusieurs suivis d'un même épisode. Elle comporte six écrans : vue d'ensemble, fiches équipements, incidents, cas similaires, questions et bibliothèque. Les données personnelles sont isolées dans un espace distinct des scénarios fictifs.

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

Les **30 rapports fictifs de l'atelier Horizon** sont chargés au démarrage. Les 12 fiches historiques du TD sont conservées séparément pour les tests de non-régression.

1. Vérifier le message **Modèle local prêt · aucun frais d'API** dans la colonne de gauche.
2. Laisser **Rédiger les réponses sur cet ordinateur** activé.
3. Dans **Incidents**, ouvrir INC114 : la lubrification n'a pas résolu les vibrations ; un réalignement ultérieur a permis une résolution confirmée. Les deux rapports restent visibles.
4. Dans **Questions**, demander « L'incident INC104 est-il résolu ? » : le statut doit provenir du suivi daté du 8 mars 2026, avec ses sources, et non du premier rapport non résolu.
5. Essayer « Quelle panne sur P999 ? » : aucune machine connue ne doit être substituée.
6. Passer à **Mes documents**, puis importer ses rapports dans la colonne de gauche. Les informations détectées restent à vérifier dans **Documents** et sont exclues des vues métier par défaut.

### Parcours de démonstration

| Écran | Ce qu'il permet de vérifier |
|---|---|
| Vue d'ensemble | 30 rapports, 10 équipements, 22 incidents et leur dernier état documenté |
| Équipements | Composition, appellations et incidents associés à une machine |
| Incidents | Étapes successives, évolution du diagnostic, actions et résultats avec preuves |
| Cas similaires | Recherche par symptôme, catégorie de composant, type de machine et résultat ; comparaison entre équipements |
| Questions | Réponse sourcée, faits observés, diagnostic, actions, résultats et informations manquantes |
| Documents | Lecture intégrale, recherche, export d'inventaire, corrections sourcées et validation humaine |

Pour essayer les cas similaires, partir d'INC116, sélectionner **Vibration** et **Roulement**, puis consulter les incidents d'autres équipements. Une ressemblance n'est pas une preuve de cause commune.

### Corriger les informations d'un import

Dans **Documents**, choisir un rapport, ouvrir **Corriger une information et vérifier sa source**, sélectionner le champ et copier une valeur avec l'extrait qui la contient. La valeur doit être présente dans l'extrait et l'extrait dans la page sélectionnée. Une correction remet la fiche à vérifier. Le bouton **Valider les informations présentes** permet ensuite son inclusion dans les vues métier.

L'extraction est conservatrice : elle reconnaît les rubriques explicites (Incident, Équipement, Date, Composant, Symptômes, Diagnostic, Statut du diagnostic, Intervention, Durée, Résultat, Constat de contrôle) et les identifiants non ambigus. Un rapport libre sans ces rubriques peut nécessiter une saisie manuelle sourcée. Aucun diagnostic n'est déduit d'un symptôme. Les validations et les corrections sont sauvegardées sur l'ordinateur après chaque modification, sans modifier le fichier original.

### Retrouver son travail et restaurer une sauvegarde

Les textes extraits, les repères de page, les corrections, les validations et les retraits sont conservés automatiquement dans `data/private/espaces.sqlite3`. Ils sont rechargés après la fermeture du navigateur ou le redémarrage de l'application. Les PDF originaux ne sont pas copiés : conserve-les séparément. Le dossier privé est exclu de GitHub ; l'historique des questions reste dans la session.

Dans la colonne de gauche, ouvrir **Sauvegarde de cet espace** :

1. **Exporter cet espace** télécharge une sauvegarde JSON de l'espace actif, avec ses textes et corrections.
2. Pour la récupérer sur une autre installation, choisir le même espace, puis ajouter le JSON dans **Restaurer une sauvegarde JSON**.
3. Vérifier le nombre de rapports proposés, puis cliquer sur **Fusionner la sauvegarde**. Les documents déjà présents et leurs fiches restent inchangés ; seuls les documents absents sont ajoutés. Pour restaurer une ancienne correction d'un rapport existant, exporter d'abord l'état actuel, retirer ce rapport dans Documents, puis restaurer la sauvegarde souhaitée.
4. Vérifier les fiches ajoutées dans **Documents** : une validation indiquée par un fichier importé n'est pas reprise automatiquement. Les validations conservées directement sur cet ordinateur restent actives après redémarrage.

Les sauvegardes contiennent les textes des rapports : conserve-les dans un emplacement approprié. Le stockage local n'est pas chiffré par l'application. Une limite de 100 Mo s'applique à chaque espace sauvegardé et à chaque fichier de restauration. Si deux onglets modifient le même espace, une écriture périmée est refusée et la version enregistrée est rechargée ; recommencer la modification après rechargement de la page.

La première génération peut être plus lente pendant le chargement du modèle. Décoche la rédaction locale pour afficher uniquement les extraits. Une synthèse sans références valides est remplacée par les sources.

## Fonctionnalités

- Import de PDF contenant du texte, TXT et Markdown.
- Découpage avec conservation du document, de la page et du numéro de passage.
- Recherche BM25, filtres par équipement et respect des références explicites.
- Recherche hybride facultative avec embeddings multilingues calculés localement.
- Synthèses du modèle local et réponses structurées à partir des fiches vérifiées, avec citations `[S1]`, `[S2]`.
- Réponses de statut établies par les dates et les résultats vérifiés, sans laisser le LLM choisir arbitrairement le dernier état.
- Relations entre équipements, composants, incidents, diagnostics et interventions ; vocabulaire commun inspiré du TD, sans raisonneur OWL dans cette V2.
- Consultation des sources, export Markdown et retrait des documents.
- Sauvegarde locale automatique et export/restauration JSON de chaque espace.
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
- Les textes extraits, corrections et validations restent sur cet ordinateur dans `data/private/`, exclu de Git. Aucun rapport n'est envoyé sur GitHub. L'historique des questions reste en mémoire dans la session.
- `.local/` contient le moteur et `.cache/` les modèles publics et les journaux techniques du moteur. Ils sont exclus de Git. L'installation d'Ollama peut aussi créer ses fichiers de fonctionnement dans `~/.ollama`.
- Le modèle peut rester chargé cinq minutes après une réponse, puis libérer sa mémoire. Le serveur local peut rester en arrière-plan pour les prochains essais.

Le coût de fonctionnement correspond aux ressources habituelles de l'ordinateur et aux téléchargements initiaux ; aucun fournisseur ne facture les questions. Un hébergement externe éventuel aurait ses propres coûts : la version documentée ici se lance sur son ordinateur.

## Vérifications

```bash
python -m pip install -r requirements-dev.txt
ruff check .
pytest -q
python -m scripts.evaluate
python -m scripts.evaluate_workshop
# Après installation du modèle d'embeddings :
python -m scripts.evaluate --semantic
python -m scripts.evaluate_workshop --semantic
# Après préparation du LLM local :
python -m scripts.validate_local
```

Voir [les vérifications réalisées](docs/VERIFICATION.md), [la fiche technique](docs/ARCHITECTURE.md), [le protocole d'essai](docs/VALIDATION.md) et [la prochaine étape](docs/ROADMAP.md).

## Limites

Cette maquette ne constitue pas une validation industrielle. Un modèle local peut se tromper et les citations doivent être relues. Le contrôle vérifie les identifiants des sources, pas l'appui de chaque affirmation.

Limites : 10 Mo et 100 pages par PDF, 30 fichiers/30 Mo par import, 100 documents et 100 Mo sauvegardés par espace. Pas d'OCR, de GMAO, d'authentification propre, de journal détaillé des validations ni de raisonnement OWL. Les espaces locaux ne constituent pas une séparation entre plusieurs utilisateurs. Les références sont repérées par des motifs simples. Les questions sont indépendantes : rappeler l'équipement à chaque fois. La recherche de cas similaires utilise un vocabulaire de symptômes et de composants et des termes communs ; les embeddings facultatifs concernent la recherche documentaire dans Questions.

GitHub héberge le code et ne fait pas tourner cette application Python. En cas de déploiement partagé, ajouter les protections et la séparation des espaces appropriées.

## Sources techniques

- [Ollama : génération locale](https://docs.ollama.com/api/chat)
- [Ollama : désactivation des fonctions cloud](https://docs.ollama.com/faq#how-do-i-disable-ollamas-cloud-features)
- [Qwen3 4B Instruct : modèle choisi](https://ollama.com/library/qwen3:4b-instruct)
- [Sentence Transformers : recherche sémantique](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html)
- [Modèle E5 multilingue](https://huggingface.co/intfloat/multilingual-e5-small)
- [Streamlit](https://docs.streamlit.io/)

Les exemples de maintenance sont des scénarios pédagogiques, pas des procédures opérationnelles.
