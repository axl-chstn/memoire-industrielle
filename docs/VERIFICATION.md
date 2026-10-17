# Vérifications de la V2 Atelier

Exécutées le 17 octobre 2026 sur un Mac Apple Silicon disposant de 8 Go de mémoire, avec Python 3.12, Ollama 0.40.5 et qwen3:4b-instruct.

| Vérification | Résultat |
|---|---|
| Analyse statique Ruff | Réussie |
| Tests automatiques | 57 réussis |
| Atelier fictif | 30 rapports, 10 équipements, 22 incidents |
| Provenance de toutes les valeurs du scénario | Chaque valeur est présente dans son extrait et l'extrait dans le document |
| Recherche et statuts documentés V2, BM25 | 13/13 cas réussis |
| Même jeu avec le vrai modèle multilingual-e5-small | 13/13 cas réussis |
| Non-régression sur les anciennes fiches du TD | 14/14 cas réussis |
| Évolution d'INC114 | Lubrification non concluante, puis réalignement et résolution confirmée |
| Dernier résultat d'INC116 | Non résolu malgré un remplacement |
| Chronologie incomplète ou contradictoire | Statut inconnu ou à clarifier ; aucune date inventée |
| Correction d'une fiche dans l'interface | Correction sourcée, retour à vérifier et nouvelle validation nécessaires |
| Espaces personnel et fictif | Documents et fiches distincts ; pas d'application des alias fictifs aux imports |
| API payante | Aucun branchement utilisé ; transport uniquement vers le modèle local |

## Essais réels du LLM local sur la V2

Trois questions libres ont été posées au modèle réellement installé :

- **Actions et résultats pour INC114** : la réponse distingue la lubrification de 25 minutes sans résolution, puis le réalignement de 75 minutes avec résolution confirmée, avec les deux sources.
- **Cause confirmée pour INC110** : la réponse conserve un diagnostic non renseigné et ne transforme pas la vibration en cause confirmée.
- **Intervention et résultat pour INC105** : remplacement du roulement et résolution confirmée, avec RAP105.

Les trois réponses ont été générées localement et relues par rapport aux extraits. Cela ne constitue pas une validation de toutes les formulations possibles. Les questions explicites de statut comme « INC104 est-il résolu ? » utilisent les fiches vérifiées et leur chronologie plutôt qu'une décision du LLM.

## Portée des tests

Les contrôles automatiques couvrent l'extraction PDF et sa page, les imports invalides, la traçabilité, les corrections, la validation humaine, les dates manquantes, les conflits de même date, les filtres, les suivis, les alias, la navigation et la génération sans clé. Un fait dont l'extrait n'apparaît pas dans le passage cité n'est pas affiché comme fait structuré sourcé.

Les 13 cas de recherche V2 portent sur les documents retrouvés et les statuts déterminés à partir des fiches. Ils ne mesurent pas la fidélité de toutes les synthèses libres. Les scénarios sont fictifs et préparés pour cette démonstration : des essais sur des rapports indépendants et auprès d'utilisateurs métier restent nécessaires.

Les documents, corrections et validations sont en mémoire dans la session, sans sauvegarde persistante. Les exports d'inventaire et de résultats sont disponibles. Le suivi des changements de fichiers de Streamlit est désactivé : redémarrer l'application après une modification du code.
