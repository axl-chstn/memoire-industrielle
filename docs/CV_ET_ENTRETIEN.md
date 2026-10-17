# Présenter le projet

## Intitulé

**Mémoire industrielle — assistant local de consultation de rapports de maintenance**

Python · Streamlit · SQLite · RAG · BM25 · Embeddings multilingues · Ollama

## Pour un CV

Développement d'un assistant local de consultation de rapports de maintenance : recherche hybride BM25/embeddings, suivi des incidents et réponses sourcées. Mise en place d'une validation humaine des informations extraites, d'une sauvegarde SQLite et de tests de régression sur des corpus fictifs. Utilisation d'un modèle local via Ollama, sans API payante.

Lien : https://github.com/axl-chstn/memoire-industrielle

Version courte : **Assistant documentaire de maintenance en Python : recherche hybride, modèle local, chronologies d'incidents et réponses traçables jusqu'aux rapports.**

## English version

Built a local maintenance-report assistant with hybrid BM25/embedding retrieval, incident timelines and source-linked answers. Added human review of extracted facts, SQLite persistence and regression tests on fictional datasets. A local Ollama model selects supporting passages; factual answers are assembled from verified records.

## En entretien · 45 secondes

« Je suis parti d'un problème de maintenance : retrouver ce qui a déjà été essayé quand une panne revient. J'ai construit une application qui organise les rapports autour des équipements et des incidents, avec une recherche par mots-clés et par le sens.

Le point qui m'a le plus intéressé est la fiabilité. Une première version pouvait mal ordonner un rapport sans date ou transformer une information manquante en conclusion. J'ai donc conservé des faits vérifiés, leur preuve et des règles explicites pour les chronologies. Le modèle local sélectionne des passages plutôt que de rédiger librement.

Aujourd'hui, le parcours fonctionne sur des rapports fictifs et dispose de tests. La suite envisagée serait d'ajouter des comptes rendus oraux, transcrits puis validés avant leur entrée dans la base. »

## Points à savoir expliquer

- Pourquoi BM25 reste utile pour les identifiants et pourquoi E5 complète la recherche.
- Pourquoi une intervention et une résolution sont deux informations différentes.
- Comment une valeur conserve sa preuve et sa page d'origine.
- Pourquoi les scores des jeux connus ne prédisent pas la qualité sur de nouveaux rapports.
- Ce qui a été réalisé avec une assistance IA : pouvoir expliquer les décisions et les limites compte davantage que revendiquer tout le code comme écrit seul.

## Partager le projet

Le PDF de trois pages peut être joint à la rubrique Projets de LinkedIn. Le dépôt GitHub apporte les détails techniques ; vérifier son accès sans connexion une fois sa publication effectuée. Les rapports privés, bases SQLite, exports et clés ne font pas partie des livrables de présentation.

Cette présentation porte sur le dépôt du projet. Elle ne prétend pas modifier les épingles ou le profil personnel GitHub.
