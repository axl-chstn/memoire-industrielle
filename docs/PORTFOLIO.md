# Mémoire industrielle - présentation du projet

**Axel Chasteauneuf** · Élève ingénieur à Mines Nancy · Data, IA et aide à la décision.

## Le problème et la solution

Lorsqu’une panne revient, retrouver ce qui a déjà été tenté demande de reconstituer plusieurs rapports. Le prototype organise les documents autour des équipements et incidents, distingue les interventions de leurs résultats et relie les réponses aux passages sources.

## Contribution et méthode

Le projet est initié et piloté par Axel Chasteauneuf : cadrage du besoin, formation au RAG, conduite du développement assisté par IA, examen des réponses et évolution des règles de fiabilité. Le code, les tests et la documentation ont été construits avec assistance IA ; cette présentation ne revendique pas une écriture manuelle et individuelle de tout le code.

## Apprentissage

Formation IBM SkillsBuild **Retrieval-Augmented Generation for Enhanced AI Outputs**, avec badge obtenu en octobre 2026, et mise en pratique initiale sur Google Colab. La [description du badge IBM](https://www.credly.com/org/ibm/badge/retrieval-augmented-generation-for-enhanced-ai-outp) présente le programme ; le justificatif personnel figure sur le [profil LinkedIn](https://www.linkedin.com/in/axel-chasteauneuf-910091388/).

## Démonstration et compétences

- [Un incident, deux interventions et leurs sources](DEMO.md).
- Python, Streamlit, SQLite, recherche BM25 et embeddings E5, modèle local via Ollama.
- [Ontologie pédagogique de maintenance](ontologie/README.md) sous Protégé/OWL, avec exemples de requêtes et inférences. Le raisonneur OWL reste séparé de l’application.
- [108 tests automatisés dans le relevé du 17 octobre 2026](RESULTATS.md). Les données sont fictives ; les résultats connus ne mesurent pas une précision générale.

## Consulter les supports

- [Présentation PDF de trois pages pour les recruteurs](Memoire_industrielle_Presentation_LinkedIn_Axel_Chasteauneuf.pdf).
- [Présentation HTML autonome](presentation-projet.html).
- [Architecture](ARCHITECTURE.md), [installation](INSTALLATION.md) et [limites des résultats](RESULTATS.md) pour approfondir.
- [Textes personnels pour le CV et l’entretien](CV_ET_ENTRETIEN.md).

Le PDF peut être joint directement à une fiche Projet LinkedIn et se lit sans installation. Le lien GitHub permet d’approfondir le code et les choix techniques lorsque le dépôt est public. Aucun document industriel privé ne figure dans la présentation.

## Perspectives

Comptes rendus oraux : transcription, brouillon modifiable puis validation humaine. Cette chaîne n’est pas implémentée. L’usage B2B en PME est une hypothèse à confronter aux utilisateurs ; aucun gain de temps métier ni déploiement industriel n’est revendiqué.
