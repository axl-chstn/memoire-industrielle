# Vérifications de cette première version

Exécutées le 17 octobre 2026 sur macOS, Python 3.12.

| Vérification | Résultat |
|---|---|
| Analyse statique Ruff | Réussie |
| Tests automatiques | 20 réussis |
| Recherche BM25 sur les questions de démonstration | 14/14 cas réussis |
| Recherche hybride avec le vrai modèle multilingual-e5-small | 14/14 cas réussis |
| Parcours dans le navigateur, sans clé API | Question sur INC07, consultation de RAP07 et résultat inconnu préservé |
| Parcours dans le navigateur avec embeddings | Mode « Sens + mots-clés » confirmé, RAP07 retrouvé |

**Génération réelle par l'API : non exécutée**, faute de clé API fournie. L'appel et les contrôles de citations sont testés avec un double de test. Une vérification avec une clé disposant de crédits et une relecture des réponses sont nécessaires pour valider la synthèse de bout en bout.

Ces résultats portent sur des scénarios fictifs et ne constituent pas une validation auprès de techniciens ou de PME. Les 14 cas de recherche mesurent le retour des sources attendues dans les trois premiers résultats, ou l'absence de résultat pour les cas négatifs ; ils ne mesurent pas la fidélité des phrases générées.

Le suivi automatique des changements de fichiers de Streamlit est désactivé pour éviter des interactions inutiles avec les modules chargés à la demande par Transformers. Après une modification du code, redémarrer l'application.
