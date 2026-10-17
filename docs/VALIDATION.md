# Essayer et évaluer la V2

## Parcours fonctionnel sur l'atelier fictif

1. Ouvrir la vue d'ensemble : 30 rapports, 10 équipements, 22 incidents ; 17 résolus, un non résolu, quatre inconnus au dernier état du scénario.
2. Dans Équipements, choisir P04, puis l'incident INC114. La lubrification du 12 février n'a pas résolu les vibrations. Le réalignement du 20 mars est suivi d'une résolution confirmée. Les deux preuves doivent rester visibles.
3. Dans Cas similaires, partir d'INC116 et rechercher Vibration + Roulement. Consulter les précédents d'autres machines, leurs tentatives et leurs résultats.
4. Dans Questions, demander « L'incident INC104 est-il résolu ? ». La réponse doit utiliser le suivi RAP121 du 8 mars, tout en conservant RAP104.
5. Demander « L'incident INC116 est-il résolu ? ». Un remplacement ne doit pas devenir une preuve de résolution : RAP128 indique des vibrations persistantes.
6. Demander « Quel est l'état de résolution d'INC117 ? ». Le résultat reste inconnu et la date ne doit pas être inventée.
7. Dans Documents, rechercher un rapport, lire le texte et consulter sa fiche. Une correction doit contenir une valeur et un extrait exacts de la page. La fiche est remise à vérifier, puis peut être validée à nouveau.
8. Passer à Mes documents : l'espace commence vide et ne reprend ni les incidents ni les alias du scénario fictif. Une fiche importée n'entre pas dans les vues métier sans vérification, sauf option explicite d'affichage des brouillons.

## Contrôles reproductibles

- `pytest -q` : extraction, sources, chronologie, contradictions, filtres, espaces séparés, navigation, corrections et transport local sans API payante.
- `python -m scripts.evaluate` : 14 questions sur les anciennes fiches du TD, conservées comme non-régression.
- `python -m scripts.evaluate_workshop` : 13 cas sur la V2, portant sur les sources retrouvées, les alias et les statuts documentés.
- `python -m scripts.evaluate_workshop --semantic` : même jeu avec le vrai modèle d'embeddings, après installation des prérequis.

Ces évaluations ne mesurent pas la fidélité de toutes les synthèses libres. Pour un essai réel du LLM local, vérifier manuellement :

| Question | Attente |
|---|---|
| Quelles actions ont été réalisées pour INC114 et quels résultats ont été constatés ? | Lubrification sans résolution, puis réalignement avec résolution confirmée ; ne pas inverser les étapes |
| Quelle cause a été confirmée pour INC110 ? | Aucune cause renseignée ; ne pas transformer la vibration en diagnostic |
| Quelle intervention et quel résultat pour INC105 ? | Remplacement du roulement et résolution confirmée avec source RAP105 |
| Quelle panne sur P999 ? | Aucun équipement connu ne doit être substitué |

Ajouter aussi un document contenant une instruction visant à inventer une résolution ; contrôler que la réponse n'obéit pas à cette instruction. Le prompt et les citations ne garantissent pas une résistance complète aux injections ni une interprétation correcte de chaque phrase.

## Documents réels

Préparer les questions et passages attendus avant les essais. Conserver des questions à l'écart des réglages pour éviter de simplement adapter le moteur aux exemples. Mesurer pertinence des sources, bonne machine, bon incident, ordre des événements, conservation des inconnues et fidélité de la synthèse. Faire ensuite tester une recherche concrète à un utilisateur métier.
