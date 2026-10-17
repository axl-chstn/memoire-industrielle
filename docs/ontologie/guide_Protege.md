# Ouvrir et démontrer le projet dans Protégé 5.6.9

## Première ouverture

1. Conserver le fichier `maintenance_industrielle.owl` dans un dossier de travail. Il est autonome : aucun import distant, aucune clé API et aucun plugin à télécharger.
2. Dans Protégé : **File > Open…**, puis choisir ce fichier. Ouvrir une nouvelle fenêtre si une autre ontologie est déjà en cours de travail.
3. Dans **Reasoner**, sélectionner **HermiT**, puis **Start reasoner**. La capture fournie confirme que HermiT et DL Query sont installés.
4. Aller dans **Entities > Classes**. Examiner **Asserted**, puis **Inferred** : les inclusions calculées apparaissent après raisonnement.
5. Si nécessaire, afficher **DL Query** depuis **Window > Tabs > DL Query**. Les identifiants et les labels sont identiques, sans accents, pour pouvoir copier les requêtes ci-dessous.
6. Cocher **Instances**, coller une expression et choisir **Execute**. Relancer ou synchroniser HermiT après toute modification.

## Parcours guidé

- `P01` est une Pompe, donc un Equipement, donc un ObjetMateriel. C’est toujours la même entité.
- `P01_RA` est un Roulement distinct. Il fait partie de `P01` : ce lien n’est pas une inclusion.
- Comparer `IncidentVibrationSeule` et `IncidentSymptomesVibroAcoustiques` dans la hiérarchie inférée. Leur inclusion est déduite des définitions.
- Pour `P02`, le roulement `P02_RA` se trouve dans `P02_PALIER`. Le raisonneur retrouve indirectement la pompe depuis `INC10`.
- `INT01 resout INC01` permet de déduire `INC01 estResoluPar INT01` et l’appartenance à `IncidentResolu`.
- `INC10` n’est ni prouvé résolu ni prouvé non résolu. `INC11` est explicitement non résolu. Leur différence est volontaire.

## Requêtes vérifiées

### Q1 - Quels équipements contiennent un roulement, même indirectement ?

```text
EquipementAvecRoulement
```

Résultat : C01, C02, M01, M02, P01, P02.

### Q2 - Quels équipements ont au moins deux roulements directs distincts ?

```text
EquipementDeuxRoulementsDirects
```

Résultat : C01, C02, M01, M02, P01.

### Q3 - Quels incidents de roulement affectent une pompe ?

```text
IncidentRoulement and IncidentPompe
```

Résultat : INC01, INC10.

### Q4 - Quels incidents critiques ont une résolution confirmée ?

```text
IncidentCritique and IncidentResolu
```

Résultat : INC01, INC05, INC06, INC08.

### Q5 - Quels rapports documentent un incident critique ?

```text
RapportCritique
```

Résultat : RAP01, RAP05, RAP06, RAP08.

### Q6 - Quels incidents ont exclusivement des vibrations ou des bruits ?

```text
IncidentSymptomesVibroAcoustiques
```

Résultat : INC01, INC03, INC04, INC07, INC08, INC09, INC11.

### Q7 - Quels incidents ont exclusivement des vibrations ?

```text
IncidentVibrationSeule
```

Résultat : INC04, INC07, INC11.

### Q8 - Quels incidents sont explicitement non résolus ?

```text
IncidentNonResolu
```

Résultat : INC04, INC11.

### Q9 - Quelles interventions ont résolu un incident de roulement ?

```text
Intervention and (resout some IncidentRoulement)
```

Résultat : INT01, INT03, INT05, INT09.

### Q10 - Quels techniciens possèdent la compétence mécanique ?

```text
Technicien and (possedeCompetence value Mecanique)
```

Résultat : Alex, Sam.

### Q11 - Quels objets sont affectés par INC10, via les inverses et la composition ?

```text
ObjetMateriel and (subitIncident value INC10)
```

Résultat : P02, P02_PALIER, P02_RA.

### Q12 - Quels incidents de roulement sont résolus par un remplacement ?

```text
IncidentRoulement and (estResoluPar some Remplacement)
```

Résultat : INC01, INC05.

## Même témoin dans une restriction imbriquée

```text
Incident and (concerneComposantPrincipal some (Roulement and (faitPartieDe some Pompe)))
```

Résultat : INC01 et INC10. Les deux conditions imbriquées concernent le même roulement.

## Montrer une contradiction (sur une copie uniquement)

1. Enregistrer une copie sous un autre nom avant l’expérience.
2. Ajouter le type `Roulement` à `P01`, déjà une `Pompe`.
3. Synchroniser HermiT : la base est incohérente, car Equipement et Composant sont disjoints.
4. Retirer cette assertion ou rouvrir le fichier d’origine. Ne pas rendre la copie incohérente.

Autres expériences déjà testées en mémoire : ajouter `aCriticite Faible` à INC01 (déjà Critique), ajouter `INT11 resout INC11`, ou relier INC11 au symptôme de fuite OBS02_1 malgré sa fermeture sur une vibration.

## Questions possibles à l’oral

- Pourquoi un roulement n’est-il pas une sous-classe de pompe ? Parce que « est un » garde le même individu, alors que la composition relie deux individus.
- Pourquoi INC10 n’est-il pas non résolu ? L’absence d’une résolution renseignée n’est pas une négation en monde ouvert.
- Pourquoi utiliser `some` avec `only` ? `only` contraint les valeurs éventuelles sans garantir leur existence.
- Pourquoi déclarer les individus différents ? Deux identifiants différents ne suffisent pas en OWL à prouver deux objets distincts.
- Pourquoi affecteObjet a-t-il pour portée ObjetMateriel ? Un incident peut concerner un sous-ensemble intermédiaire sans le transformer en Equipement.
- Pourquoi HermiT et pas seulement une recherche par mots ? Les résultats exploitent des conséquences logiques non saisies directement.
- Pourquoi ne pas conclure vibration donc usure ? Le symptôme n’est pas une preuve universelle du mode de défaillance.
- Qu’est-ce qui serait à améliorer ? L’historique des montages, la gestion du temps, les causes multiples, puis la liaison aux documents réels.

## Avant remise

La date officielle et la durée de l’oral doivent être confirmées. Ajouter les noms du binôme au rapport, vérifier les règles du cours sur l’assistance IA et s’assurer que chacun sait modifier une définition, exécuter une requête et expliquer un contre-exemple.
