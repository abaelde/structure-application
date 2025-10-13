# Engine Module Architecture

Le module `engine` est responsable du calcul des cessions de réassurance. Il a été refactoré pour une meilleure séparation des responsabilités et une maintenabilité améliorée.

## Structure du Module

```
src/engine/
├── __init__.py                  # Exports publics
├── calculation_engine.py        # Orchestrateur principal
├── section_matcher.py          # Logique de matching
├── policy_lifecycle.py         # Gestion du cycle de vie des polices
├── cession_calculator.py       # Calculs de cession
├── structure_orchestrator.py   # Orchestration des structures
├── bordereau_processor.py      # Traitement batch
└── treaty_manager.py           # Gestion des traités multi-années
```

## Responsabilités

### `calculation_engine.py`
**Rôle** : Orchestrateur principal de l'application d'un programme à une police

**Fonctions publiques** :
- `apply_program(policy_data, program, calculation_date)` : Applique un programme à une police

**Responsabilités** :
- Coordonner les différents composants
- Vérifier le statut de la police (active/inactive)
- Vérifier les exclusions
- Orchestrer le traitement des structures
- Construire le résultat final

### `section_matcher.py`
**Rôle** : Logique de matching entre polices et sections

**Fonctions** :
- `check_exclusion(policy_data, sections, dimension_columns)` : Vérifie si une police est exclue
- `match_section(policy_data, sections, dimension_columns)` : Trouve la section la plus spécifique pour une police

**Responsabilités** :
- Évaluer les conditions de matching
- Calculer la spécificité des sections
- Identifier les exclusions

### `policy_lifecycle.py`
**Rôle** : Gestion du cycle de vie des polices (expiration, statuts)

**Fonctions publiques** :
- `check_policy_status(policy_data, calculation_date)` : Vérifie si une police est active
- `create_inactive_result(policy_data, inactive_reason)` : Crée un résultat pour une police inactive
- `create_excluded_result(policy_data)` : Crée un résultat pour une police exclue

**Fonctions internes** :
- `create_non_covered_result(policy_data, exclusion_status, exclusion_reason)` : Fonction générique pour créer un résultat de police non couverte

**Responsabilités** :
- Vérifier les dates d'expiration
- Générer les résultats pour polices inactives
- Générer les résultats pour polices exclues
- Factoriser la création de résultats "zero cession" (DRY principle)

### `cession_calculator.py`
**Rôle** : Calculs mathématiques purs des cessions

**Fonctions** :
- `apply_section(exposure, section, type_of_participation)` : Calcule la cession pour une section

**Responsabilités** :
- Appliquer les formules de quota share
- Appliquer les formules d'excess of loss
- Calculer la part réassureur

### `structure_orchestrator.py`
**Rôle** : Orchestration du traitement des structures (chaînage, rescaling)

**Fonctions** :
- `process_structures(structures, policy_data, dimension_columns, exposure)` : Traite toutes les structures

**Fonctions internes** :
- `_calculate_input_exposure()` : Calcule l'exposition d'entrée pour une structure
- `_rescale_section_if_needed()` : Rescale les sections XL après QS
- `_calculate_retention_pct()` : Calcule le pourcentage de rétention
- `_add_unapplied_structure_detail()` : Ajoute les détails d'une structure non appliquée
- `_add_applied_structure_detail()` : Ajoute les détails d'une structure appliquée

**Responsabilités** :
- Gérer les dépendances entre structures (predecessor)
- Rescaler les paramètres XL après une QS
- Traiter les structures dans le bon ordre
- Calculer les totaux

### `bordereau_processor.py`
**Rôle** : Traitement batch de bordereaux

**Fonctions** :
- `apply_program_to_bordereau(bordereau_df, program, calculation_date)` : Applique un programme à un bordereau
- `apply_treaty_with_claim_basis(policy_data, treaty_manager, calculation_date)` : Applique un traité avec claim basis
- `apply_treaty_manager_to_bordereau(bordereau_df, treaty_manager, calculation_date)` : Applique un treaty manager à un bordereau

**Responsabilités** :
- Itérer sur les polices d'un bordereau
- Gérer les traités multi-années
- Convertir les résultats en DataFrame

### `treaty_manager.py`
**Rôle** : Gestion des traités multi-années

**Classes** :
- `TreatyManager` : Gère plusieurs traités par année

**Responsabilités** :
- Stocker plusieurs versions de traités
- Sélectionner le bon traité selon claim basis et dates
- Gérer les traités risk attaching vs losses occurring

## Flux de Données

### Application d'un programme à une police

```
policy_data + program
        ↓
calculation_engine.apply_program()
        ↓
    ┌───┴───────────────────────────┐
    │                               │
policy_lifecycle.check_policy_status()
    │
    ├─ inactive? → create_inactive_result()
    │
section_matcher.check_exclusion()
    │
    ├─ excluded? → create_excluded_result()
    │
structure_orchestrator.process_structures()
    │
    ├─ section_matcher.match_section()
    ├─ cession_calculator.apply_section()
    └─ _rescale_section_if_needed()
        ↓
    result_dict
```

### Application à un bordereau

```
bordereau_df + program
        ↓
bordereau_processor.apply_program_to_bordereau()
        ↓
    for each row:
        calculation_engine.apply_program()
        ↓
    results_df
```

## Exports Publics

Le module exporte les fonctions suivantes via `__init__.py` :

```python
from src.engine import (
    apply_program,                      # calculation_engine
    apply_program_to_bordereau,         # bordereau_processor
    apply_treaty_with_claim_basis,      # bordereau_processor
    apply_treaty_manager_to_bordereau,  # bordereau_processor
    TreatyManager,                      # treaty_manager
    create_treaty_manager_from_directory, # treaty_manager
)
```

## Avantages du Refactoring

### Séparation des Responsabilités
- Chaque module a une responsabilité claire et unique
- Facilite la compréhension du code
- Réduit le couplage entre composants

### Testabilité
- Chaque module peut être testé indépendamment
- Facilite les tests unitaires
- Permet les mocks et stubs

### Maintenabilité
- Modifications localisées (un changement dans le matching n'affecte pas les calculs)
- Fichiers plus courts et plus lisibles
- Réutilisabilité accrue

### Extensibilité
- Facile d'ajouter de nouveaux types de calculs
- Nouveau mécanisme de matching peut être ajouté sans toucher aux autres modules
- Support de nouveaux types de traités facilité

## Migration

### Ancien Code
```python
from src.engine.calculation_engine import (
    apply_program,
    apply_program_to_bordereau,
    check_exclusion,
    match_section,
)
```

### Nouveau Code
```python
# Import via le module principal (recommandé)
from src.engine import (
    apply_program,
    apply_program_to_bordereau,
)

# Ou import direct si besoin d'accéder aux sous-modules
from src.engine.section_matcher import check_exclusion, match_section
```

## Compatibilité

Le refactoring est **rétro-compatible** :
- Toutes les fonctions publiques sont toujours accessibles via `src.engine`
- Les signatures de fonctions n'ont pas changé
- Les résultats sont identiques

Les seuls changements nécessaires concernent les imports directs depuis `calculation_engine` qui doivent maintenant utiliser les modules spécialisés.

