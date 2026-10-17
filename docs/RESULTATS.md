# Résultats des vérifications

**Relevé du 17 octobre 2026.** Les vérifications ci-dessous ont été exécutées, pas seulement prévues dans la documentation. Les résultats chiffrés concernent les jeux fictifs fournis. Le [relevé JSON](resultats-tests.json) conserve les commandes, résultats et empreintes des lockfiles. Le [journal historique](VERIFICATION.md) détaille les corrections précédentes.

## Installation et tests sans modèle

Une installation a été créée dans un environnement neuf, avec Python 3.12, `scripts.bootstrap --dev` et les dépendances verrouillées. `pip check` ne signale aucun conflit. Les contrôles suivants ont été exécutés avec cet environnement :

| Vérification | Résultat observé | Ce qui est contrôlé |
|---|---|---|
| Ruff | Réussi | Erreurs de code et imports couverts par la configuration |
| Pytest | **108 tests réussis**, 0 échec | Extraction, citations, chronologie, réponses, stockage et parcours Streamlit |
| Corpus historique | **14/14** | Rapports retrouvés et cas sans source |
| Atelier Horizon, BM25 | **13/13** | Sources attendues et états documentés des incidents |
| Atelier des Rives | **20/20** | Repères de réponse et sources de régressions connues |

Pytest a terminé en 9,72 secondes sur cette exécution. Ce temps est un relevé de test, pas une promesse de performance de l'application.

## Options locales

| Essai | Résultat | Portée |
|---|---|---|
| Horizon, recherche hybride | **13/13**, E5 réellement chargé depuis le cache, mode hors ligne | Recherche et statuts sur le même jeu connu |
| `validate_local` | **3/3** sélections de passages littéraux par Qwen | Le modèle répond en JSON et les passages contrôlés sont affichés ; leur pertinence doit toujours être relue |
| Rives avec `--local` | **20/20** | Sur cette exécution, les réponses utilisent les chemins structurés ou bornés : ce score ne mesure donc pas la sélection libre du LLM |
| Lockfile sémantique | Résolution à blanc réussie sur le Mac | La recherche hybride a été essayée dans l'environnement local existant, pas réinstallée entièrement dans l'environnement neuf |

Les captures de la [démonstration](DEMO.md) proviennent de l'application : INC114 conserve ses deux interventions et INC117 reste inconnu. Elles ne sont pas des maquettes graphiques.

## Environnement de référence

- macOS, Apple Silicon, 8 Go de RAM ; Python 3.12.
- Environnement neuf : Streamlit 1.66.0, NumPy 2.5.4, pypdf 6.21.1, pytest 9.1.1, Ruff 0.17.1.
- Options locales : sentence-transformers 5.7.0, PyTorch 2.14.1 ; `intfloat/multilingual-e5-small`.
- Modèle local : `qwen3:4b-instruct`, moteur Ollama 0.40.5. Couche GGUF observée : `sha256:85e4a5b7b8ef0e48af0e8658f5aaab9c2324c76c1641493f4d1e25fce54b18b9`.

La base documentaire personnelle n'a pas été utilisée pour les captures du portfolio. Les tests d'interface isolent leur stockage dans des dossiers temporaires.

## Relancer les vérifications

L'[installation](INSTALLATION.md) fournit les commandes, y compris la vérification dans un environnement neuf. Le [workflow GitHub](../.github/workflows/checks.yml) installe le verrou de développement puis exécute Ruff, pytest et les trois évaluations sans modèle. Consulter son [état réel dans Actions](https://github.com/axl-chstn/memoire-industrielle/actions/workflows/checks.yml) ; un résultat local réussi ne suffit pas à affirmer qu'un job distant est passé.

## Interpréter les chiffres

Les vingt questions des Rives ont servi à corriger des erreurs : elles ne sont plus un jeu indépendant. Les scripts vérifient des sources, des statuts et des repères de texte, pas toutes les nuances d'une réponse. Les 108 tests comprennent des contrôles du contrat du modèle avec des réponses simulées ; ils ne représentent pas 108 échanges avec Qwen.

Ces résultats ne démontrent pas une précision de 100 % sur de nouveaux documents, une fiabilité de diagnostic, un gain de temps métier ou une aptitude à la production. Ces points nécessiteraient une évaluation indépendante qui n'est pas engagée à cette étape.
