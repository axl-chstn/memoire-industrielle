# Installer et vérifier

La référence est **Python 3.12**. Les dépendances directes et transitives sont fixées dans les fichiers `.lock`, avec leurs empreintes SHA-256. Le script d'installation crée un environnement isolé et demande à pip de contrôler ces empreintes. Les fichiers `requirements*.txt` décrivent les plages de développement ; ils ne sont pas le chemin d'installation de référence.

## Parcours rapide

```bash
git clone https://github.com/axl-chstn/memoire-industrielle.git
cd memoire-industrielle
python3.12 -m scripts.bootstrap --run
```

Sous Windows : `py -3.12 -m scripts.bootstrap --run`. Aucun modèle n'est téléchargé par cette commande. Elle permet la consultation, les fiches sourcées et la recherche BM25. Ouvrir ensuite http://127.0.0.1:8501. Arrêter le serveur avec Ctrl+C.

L'environnement `.venv` est réutilisé aux prochains lancements. Les documents existants sont conservés. Pour lancer sans réinstaller :

```bash
# macOS/Linux
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
# Windows
.venv\Scripts\python -m streamlit run app.py --server.address 127.0.0.1
```

Sur Mac, `Lancer.command` reste un raccourci : il installe les dépendances verrouillées, prépare aussi le modèle puis démarre l'application. Il demande donc davantage de temps et d'espace au premier lancement.

## Recherche hybride et modèle local

```bash
python3.12 -m scripts.bootstrap --semantic --model --run
```

Sur Windows/Linux, installer d'abord Ollama depuis https://ollama.com/download. Sur Mac, le script peut télécharger le moteur depuis la source officielle. Les options sont indépendantes : `--semantic` installe les embeddings, `--model` prépare Qwen. On peut les lancer séparément.

Dans l'application, cocher **Chercher aussi par le sens**. Le premier calcul télécharge `intfloat/multilingual-e5-small`. Qwen `qwen3:4b-instruct` occupe environ 2,5 Go. Prévoir plusieurs Go supplémentaires pour les bibliothèques et caches. Les essais locaux ont été faits sur Mac Apple Silicon avec 8 Go de RAM ; cela ne constitue pas une configuration minimale garantie pour d'autres machines.

Le moteur du projet écoute sur `127.0.0.1:11435`, avec les fonctions cloud désactivées. Il ne bascule pas vers une API payante. Sans modèle prêt, les fiches et les sources restent consultables. Après les téléchargements, aucune connexion n'est requise pour le calcul local ; ne pas confondre ce fonctionnement avec une certification d'isolation réseau.

Les poids et le moteur ne sont pas contenus dans les lockfiles Python. Le nom d'un modèle téléchargé peut évoluer côté distributeur ; les sorties du LLM peuvent aussi varier. Les tests du dépôt vérifient les contrats de réponse et les faits attendus, pas une identité de texte entre toutes les machines.

## Vérifier une installation neuve

```bash
python3.12 -m scripts.bootstrap --dev --venv .cache/installation-verifiee
.cache/installation-verifiee/bin/python -m pip check
.cache/installation-verifiee/bin/python -m ruff check .
.cache/installation-verifiee/bin/python -m pytest -q
.cache/installation-verifiee/bin/python -m scripts.evaluate
.cache/installation-verifiee/bin/python -m scripts.evaluate_workshop
.cache/installation-verifiee/bin/python -m scripts.evaluate_rives
```

Sous Windows, remplacer `bin/python` par `Scripts/python.exe`. Cette vérification n'exige ni modèle ni clé. Le workflow GitHub reprend les vérifications sur Ubuntu/Python 3.12. L'environnement Dev Container est fourni pour faciliter l'ouverture du code ; sa présence ne vaut pas un essai manuel sous chaque OS.

Après installation des modèles, les essais locaux complémentaires sont :

```bash
.venv/bin/python -m scripts.evaluate_workshop --semantic
.venv/bin/python -m scripts.validate_local
.venv/bin/python -m scripts.evaluate_rives --local
```

## Données et problèmes courants

- **Python différent de 3.12** : utiliser l'interpréteur 3.12 pour l'installation verrouillée ; le script refuse les autres versions plutôt que de promettre un environnement non testé.
- **Port 8501 occupé** : fermer le serveur précédent, ou lancer Streamlit avec `--server.port 8502`.
- **Modèle indisponible** : relancer `.venv/bin/python -m scripts.local_runtime`. Les téléchargements nécessitent Internet et de la place sur le disque.
- **Embeddings non disponibles** : relancer l'installation avec `--semantic` ; la recherche BM25 reste utilisable sans cette option.
- **Rapports après redémarrage** : relancer depuis le même dossier. Les textes et fiches sont dans `data/private/espaces.sqlite3`. Ne pas supprimer ce dossier pour réparer un problème d'installation.
- **Sauvegarde** : exporter l'espace depuis l'interface et conserver les PDF originaux à part. Ne pas déposer la base locale ni les exports personnels dans GitHub.

## Mettre à jour les dépendances

Pour une évolution du projet, modifier les plages `.txt`, puis régénérer les trois lockfiles avec `uv pip compile --universal --python-version 3.12 --generate-hashes`, en passant le fichier `.txt` et `--output-file` correspondant. Réinstaller dans un environnement neuf et relancer les tests avant de publier les nouvelles versions. Cette étape est destinée au développement ; uv n'est pas nécessaire pour essayer le projet.
