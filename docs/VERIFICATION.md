# Vérifications de la V2 Atelier

Exécutées le 17 octobre 2026 sur un Mac Apple Silicon disposant de 8 Go de mémoire, avec Python 3.12, Ollama 0.40.5 et qwen3:4b-instruct.

| Vérification | Résultat |
|---|---|
| Analyse statique Ruff | Réussie |
| Tests automatiques après correction de la fiabilité | 108 réussis |
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
| Nouvelle session et redémarrage du stockage | Textes, pages, corrections et validations conservés |
| Retrait de documents | Persistant, sans rechargement automatique des documents retirés |
| Deux onglets modifiant un espace | Écriture périmée refusée, version sauvegardée rechargée |
| Sauvegarde JSON | Fusion additive ; documents existants et corrections conservés |
| Fichier de sauvegarde importé | Fiches remises à vérifier ; preuves invalides et faux documents fictifs refusés |
| Écriture invalide ou base illisible | Version précédente conservée ; aucune remise à zéro automatique |

## Essais réels avant la correction de la fiabilité

Trois questions libres ont été posées au modèle réellement installé :

- **Actions et résultats pour INC114** : la réponse distingue la lubrification de 25 minutes sans résolution, puis le réalignement de 75 minutes avec résolution confirmée, avec les deux sources.
- **Cause confirmée pour INC110** : la réponse conserve un diagnostic non renseigné et ne transforme pas la vibration en cause confirmée.
- **Intervention et résultat pour INC105** : remplacement du roulement et résolution confirmée, avec RAP105.

Les trois réponses ont été générées localement et relues par rapport aux extraits. Cela ne constitue pas une validation de toutes les formulations possibles. Les questions explicites de statut comme « INC104 est-il résolu ? » utilisent les fiches vérifiées et leur chronologie plutôt qu'une décision du LLM.

## Portée des tests

Les contrôles automatiques couvrent l'extraction PDF et sa page, les imports invalides, la traçabilité, les corrections, la validation humaine, les dates manquantes, les conflits de même date, les filtres, les suivis, les alias, la navigation et la génération sans clé. Un fait dont l'extrait n'apparaît pas dans le passage cité n'est pas affiché comme fait structuré sourcé.

Les 13 cas de recherche V2 portent sur les documents retrouvés et les statuts déterminés à partir des fiches. Ils ne mesurent pas la fidélité de toutes les synthèses libres. Les scénarios sont fictifs et préparés pour cette démonstration : des essais sur des rapports indépendants et auprès d'utilisateurs métier restent nécessaires.

Les tests de sauvegarde utilisent des dossiers temporaires distincts des données personnelles. Les textes extraits, corrections et validations sont conservés localement ; les PDF originaux et l'historique des questions ne sont pas inclus. Les exports d'inventaire, de résultats et d'espace restent disponibles. Le suivi des changements de fichiers de Streamlit est désactivé : redémarrer l'application après une modification du code.

Un essai dans le navigateur a également été effectué sur une instance locale avec un stockage temporaire isolé : restauration d'un rapport fictif JSON, correction sourcée de l'intervention, validation humaine, téléchargement de l'export, puis arrêt complet et redémarrage du serveur. Le rapport, la correction et sa validation étaient présents dans la nouvelle session. Le contenu du fichier téléchargé a été comparé à la fiche enregistrée. Les données personnelles de l'application principale n'ont pas été utilisées pour cet essai.

## Correction de la fiabilité — 17 octobre 2026

L’audit de vingt questions sur l’atelier fictif des Rives avait relevé quinze réponses sans anomalie factuelle, un repli vers des fiches correctes, deux réserves et deux réponses erronées ou contradictoires. Les erreurs concernaient une chronologie sans date, une intervention non renseignée transformée en absence d’intervention, un inconnu transformé en échec et des phrases supplémentaires non justifiées.

La nouvelle version compose les réponses courantes depuis les faits vérifiés et leurs preuves. Pour une question libre, le modèle peut uniquement sélectionner des identifiants de passages ; l’application recopie le texte source. Elle refuse les commentaires ajoutés, les identifiants inventés et les réponses JSON non conformes. Les fiches restent lisibles si le modèle est arrêté ou si sa sélection est refusée.

Les vingt contrôles connus sont rejoués avec `python -m scripts.evaluate_rives --local`, en utilisant le modèle réellement installé pour les questions libres. Les repères automatiques ne suffisent pas à prouver la fidélité : les réponses corrigées doivent aussi être relues. Les cas des Rives sont maintenant un jeu de régression connu, et non une validation indépendante. Des tests sur de nouveaux identifiants, dates et formulations complètent ce contrôle.
