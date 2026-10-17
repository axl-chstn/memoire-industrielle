# Vérifications de la version sans frais d'API

Exécutées le 17 octobre 2026 sur un Mac Apple Silicon disposant de 8 Go de mémoire, avec Python 3.12, Ollama 0.40.5 et le modèle qwen3:4b-instruct.

| Vérification | Résultat |
|---|---|
| Analyse statique Ruff | Réussie |
| Tests automatiques | 32 réussis |
| Recherche BM25 sur les questions de démonstration | 14/14 cas réussis |
| Recherche hybride E5 | 14/14 dans la première version ; moteur de recherche inchangé |
| Installation réelle du moteur et du LLM | Réussie, poids d'environ 2,5 Go |
| Écoute du moteur | 127.0.0.1:11435 uniquement |
| Désactivation du cloud | Message « Ollama cloud disabled: true » vérifié dans les journaux |
| Transport applicatif | Adresse locale fixe, sans clé, proxy HTTP ou suivi de redirection |
| Refus des modèles distants | Vérifié par tests avant toute transmission de la question |
| Génération réelle pour INC05 | Réponse locale : incident résolu, avec citation RAP05 |
| Génération réelle pour INC04 | Réponse locale : incident non résolu, avec citation RAP04 |
| Génération réelle pour INC07 | Le modèle a confondu inconnu et non résolu ; le garde-fou a rejeté la synthèse et conservé RAP07 |

Aucun appel à un fournisseur payant n'a été utilisé pour ces vérifications. Le branchement OpenAI et sa dépendance ont été retirés de l'application et des prérequis. Une ancienne variable de clé API n'est plus lue.

Le cas INC07 montre une limite réelle du petit modèle local : une réponse peut être incorrecte malgré des citations présentes. Le contrôle ajouté couvre cette contradiction explicite mais ne garantit pas la fidélité de toutes les autres réponses. Relire les sources reste nécessaire. Le script `python -m scripts.validate_local` reproduit les trois essais, enregistre les résultats et indique les substitutions par les extraits.

Les tests automatiques utilisent des réponses contrôlées pour vérifier le transport local, les échecs, les citations et le garde-fou. Les essais réels sont distincts. Les données restent fictives : ces résultats ne constituent pas une validation industrielle ou auprès de PME.

Le suivi des changements de fichiers de Streamlit est désactivé ; redémarrer l'application après une modification du code.
