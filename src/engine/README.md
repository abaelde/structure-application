# Engine Module Architecture

Le module `engine` est responsable du calcul des cessions de réassurance. Il a été refactoré pour une meilleure séparation des responsabilités et une maintenabilité améliorée.

## Structure du Module

```
src/engine/
├── __init__.py                  # Exports publics
├── calculation_engine.py        # Orchestrateur principal
├── condition_matcher.py          # Logique de matching
├── policy_lifecycle.py         # Gestion du cycle de vie des polices
├── cession_calculator.py       # Calculs de cession
├── structure_orchestrator.py   # Orchestration des structures
└── bordereau_processor.py      # Traitement batch
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

### `condition_matcher.py`
**Rôle** : Logique de matching entre polices et conditions

**Fonctions** :
- `check_exclusion(policy_data, conditions, dimension_columns)` : Vérifie si une police est exclue
- `match_condition(policy_data, conditions, dimension_columns)` : Trouve la condition la plus spécifique pour une police

**Responsabilités** :
- Évaluer les conditions de matching
- Calculer la spécificité des conditions
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
- `apply_condition(exposure, condition, type_of_participation)` : Calcule la cession pour une condition

**Responsabilités** :
- Appliquer les formules de quota share
- Appliquer les formules d'excess of loss
- Calculer la part réassureur

### `structure_orchestrator.py`
**Rôle** : Orchestration du traitement des structures (chaînage, rescaling)

**Fonctions** :
- `process_structures(structures, policy_data, dimension_columns, exposure)` : Traite toutes les structures

**Fonctions internes** :
- `_calculate_input_exposure()` : Calcule l'exposure d'entrée pour une structure
- `_rescale_condition_if_needed()` : Rescale les conditions XL après QS
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

**Responsabilités** :
- Itérer sur les polices d'un bordereau
- Convertir les résultats en DataFrame

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
condition_matcher.check_exclusion()
    │
    ├─ excluded? → create_excluded_result()
    │
structure_orchestrator.process_structures()
    │
    ├─ condition_matcher.match_condition()
    ├─ cession_calculator.apply_condition()
    └─ _rescale_condition_if_needed()
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
    apply_program,
    apply_program_to_bordereau,
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
    match_condition,
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
from src.engine.condition_matcher import check_exclusion, match_condition
```



## Filtrage Hull/Liability pour Aviation

### Vue d'ensemble

Le module `engine` supporte maintenant le filtrage sélectif des composantes Hull et Liability de l'exposition aviation. Cela permet de créer des structures qui ne s'appliquent que sur une partie de l'exposition totale.

### Cas d'usage

En aviation, l'exposition totale d'une police se décompose en :
- **Hull** : `HULL_LIMIT × HULL_SHARE`
- **Liability** : `LIABILITY_LIMIT × LIABILITY_SHARE`

Certaines structures de réassurance peuvent ne couvrir que :
- Hull uniquement (ex: protection spécifique sur les appareils)
- Liability uniquement (ex: protection responsabilité civile)
- Les deux (comportement par défaut)

### Configuration

Dans le fichier **conditions.csv** du programme, deux colonnes optionnelles permettent de contrôler ce filtrage :

| Colonne | Type | Défaut | Description |
|---------|------|--------|-------------|
| `INCLUDES_HULL` | Boolean | `TRUE` | Inclure la composante Hull dans cette condition |
| `INCLUDES_LIABILITY` | Boolean | `TRUE` | Inclure la composante Liability dans cette condition |

**Valeurs acceptées** : `TRUE`, `FALSE`, `true`, `false`, `1`, `0`, `yes`, `no`

### Exemple

#### Programme avec filtrage

```
Feuille "conditions":
| BUSINESS_TITLE | INCLUDES_HULL | INCLUDES_LIABILITY | CESSION_PCT | ... |
|----------------|---------------|-------------------|-------------|-----|
| QS_ALL         | TRUE          | TRUE              | 0.25        | ... |
| XOL_HULL       | TRUE          | FALSE             | NULL        | ... |
| XOL_LIABILITY  | FALSE         | TRUE              | NULL        | ... |
```

#### Calcul

Pour une police avec :
- Hull : 100M × 15% = **15M**
- Liability : 500M × 10% = **50M**
- Total : **65M**

**1. QS_ALL (25% sur tout)** :
- Input : 65M (Hull + Liability)
- Cession : 16.25M
- Retained : 48.75M

**2. XOL_HULL (Hull only)** :
- Retained total : 48.75M
- Composante Hull du retained : 48.75M × (15M / 65M) = **11.25M**
- Input XOL_HULL : 11.25M ← **Seul le Hull est injecté**
- Application de l'XoL sur 11.25M uniquement

**3. XOL_LIABILITY (Liability only)** :
- Retained total : 48.75M
- Composante Liability du retained : 48.75M × (50M / 65M) = **37.5M**
- Input XOL_LIABILITY : 37.5M ← **Seul le Liability est injecté**
- Application de l'XoL sur 37.5M uniquement

### Implémentation

#### Classe `ExposureBundle`

```python
from src.domain.exposure_bundle import ExposureBundle

bundle = ExposureBundle(total=65_000_000, components={"hull": 15_000_000, "liability": 50_000_000})

# Propriétés
bundle.total  # 65_000_000
bundle.components  # {"hull": 15_000_000, "liability": 50_000_000}

# Filtrage
bundle.select({"hull"})       # 15_000_000
bundle.select({"liability"})  # 50_000_000
bundle.total                  # 65_000_000
```

#### Calculateur d'exposition

```python
from src.domain.exposure import AviationExposureCalculator

calculator = AviationExposureCalculator()
policy_data = {
    "HULL_LIMIT": 100_000_000,
    "LIABILITY_LIMIT": 500_000_000,
    "HULL_SHARE": 0.15,
    "LIABILITY_SHARE": 0.10,
}

total = calculator.calculate(policy_data)  # 65_000_000

# Bundle avec composants détaillés (nouvelle méthode)
bundle = calculator.bundle(policy_data)
print(bundle.total)                    # 65_000_000
print(bundle.components["hull"])       # 15_000_000
print(bundle.components["liability"])  # 50_000_000
```

### Orchestration

Le module `structure_orchestrator` gère automatiquement :

1. **Décomposition de l'exposition** : L'exposition est décomposée en composantes Hull/Liability
2. **Propagation des proportions** : Après chaque structure, les proportions Hull/Liability sont maintenues
3. **Filtrage par condition** : Chaque condition filtre l'exposition selon ses flags `INCLUDES_HULL` et `INCLUDES_LIABILITY`
4. **Rescaling** : Si la condition a un predecessor de type Quota Share, l'attachment et la limite sont rescalés

### Validation

Le modèle `condition` valide automatiquement que :
- Au moins un des deux flags (`INCLUDES_HULL` ou `INCLUDES_LIABILITY`) est `True`
- Cette validation est contournée pour les conditions d'exclusion

```python
# ✅ Valide
condition({"INCLUDES_HULL": True, "INCLUDES_LIABILITY": True, "SIGNED_SHARE_PCT": 1.0})
condition({"INCLUDES_HULL": True, "INCLUDES_LIABILITY": False, "SIGNED_SHARE_PCT": 1.0})
condition({"INCLUDES_HULL": False, "INCLUDES_LIABILITY": True, "SIGNED_SHARE_PCT": 1.0})

# ❌ Invalide
condition({"INCLUDES_HULL": False, "INCLUDES_LIABILITY": False, "SIGNED_SHARE_PCT": 1.0})
# ValueError: At least one of INCLUDES_HULL or INCLUDES_LIABILITY must be True
```

### Compatibilité

- **Casualty non affecté** : Pour les programmes Casualty, ces flags sont ignorés car il n'y a qu'une seule notion d'exposition
- **Tests existants** : Tous les tests existants continuent de passer sans modification

### Exemple complet

Voir le fichier [`examples/program_creation/create_aviation_hull_liability_split.py`](../../examples/program_creation/create_aviation_hull_liability_split.py) pour un exemple complet de création d'un programme avec filtrage Hull/Liability.

## Sélection multi-année & Claim Basis (RA/LO)

### Vue d'ensemble

Le module `engine` supporte maintenant la sélection temporelle des structures basée sur le **Claim Basis** (Risk Attaching vs Loss Occurring). Cela permet de créer des programmes multi-annuels où chaque structure a sa propre période d'effet.

### Types de Claim Basis

- **Risk Attaching (RA)** : La structure s'applique si la date d'inception de la police est dans la période d'effet de la structure
- **Loss Occurring (LO)** : La structure s'applique si la date de calcul (`calculation_date`) est dans la période d'effet de la structure

### Configuration

Dans le fichier **structures.csv** du programme, les colonnes suivantes contrôlent la sélection temporelle :

| Colonne | Type | Défaut | Description |
|---------|------|--------|-------------|
| `CLAIMS_BASIS` | String | `risk_attaching` | Type de claim basis (`risk_attaching` ou `loss_occurring`) |
| `EFFECTIVE_DATE` | Date | `NULL` | Date de début d'effet de la structure |
| `INSPER_EXPIRY_DATE` | Date | `NULL` | Date de fin d'effet de la structure (exclusive) |

### Comportement

#### Risk Attaching (RA)
- **Référence** : `Policy.INCEPTION_DT`
- **Logique** : La structure s'applique si `INCEPTION_DT` ∈ `[EFFECTIVE_DATE ; INSPER_EXPIRY_DATE[`
- **Cas d'usage** : Structures qui suivent le cycle de vie de la police

#### Loss Occurring (LO)
- **Référence** : `calculation_date` (paramètre passé à `apply_program`)
- **Logique** : La structure s'applique si `calculation_date` ∈ `[EFFECTIVE_DATE ; INSPER_EXPIRY_DATE[`
- **Cas d'usage** : Structures qui s'appliquent selon la date de survenance des sinistres

### Exemple

#### Programme multi-annuel

```
Feuille "structures":
| BUSINESS_TITLE | CLAIMS_BASIS | EFFECTIVE_DATE | INSPER_EXPIRY_DATE | ... |
|----------------|----------------------|----------------------|-------------------|-----|
| QS_2024        | risk_attaching      | 2024-01-01          | 2025-01-01        | ... |
| QS_2025        | risk_attaching      | 2025-01-01          | 2026-01-01        | ... |
| XOL_2024       | loss_occurring      | 2024-01-01          | 2025-01-01        | ... |
| XOL_2025       | loss_occurring      | 2025-01-01          | 2026-01-01        | ... |
```

#### Calcul avec `calculation_date="2024-06-15"`

**Police avec `INCEPTION_DT="2024-03-01"`** :
- ✅ **QS_2024** : Applicable (RA, inception dans [2024-01-01 ; 2025-01-01[)
- ❌ **QS_2025** : Non applicable (RA, inception hors [2025-01-01 ; 2026-01-01[)
- ✅ **XOL_2024** : Applicable (LO, calculation_date dans [2024-01-01 ; 2025-01-01[)
- ❌ **XOL_2025** : Non applicable (LO, calculation_date hors [2025-01-01 ; 2026-01-01[)

**Police avec `INCEPTION_DT="2025-03-01"`** :
- ❌ **QS_2024** : Non applicable (RA, inception hors [2024-01-01 ; 2025-01-01[)
- ✅ **QS_2025** : Applicable (RA, inception dans [2025-01-01 ; 2026-01-01[)
- ✅ **XOL_2024** : Applicable (LO, calculation_date dans [2024-01-01 ; 2025-01-01[)
- ❌ **XOL_2025** : Non applicable (LO, calculation_date hors [2025-01-01 ; 2026-01-01[)

### Reporting

Les structures non applicables (hors période) sont incluses dans le rapport avec :
- `applied=False`
- `reason="out_of_period"`
- `matching_details={"claim_basis": "risk_attaching"}` ou `{"claim_basis": "loss_occurring"}`

### API

```python
from src.engine import apply_program

# Application avec date de calcul
result = apply_program(policy, program, calculation_date="2025-01-01")

# Les structures LO seront évaluées selon calculation_date
# Les structures RA seront évaluées selon policy.inception
```

### Implémentation

La logique de sélection temporelle est implémentée dans :
- `Structure.is_applicable()` : Méthode qui détermine si une structure est applicable
- `StructureProcessor.process_structures()` : Filtre les structures avant traitement
- `StructureProcessor._process_one()` : Vérification de sécurité pour les prédécesseurs

