# Tests - Structure et Organisation

## 📁 Structure des tests

```
tests/
├── conftest.py                    # Configuration pytest et fixtures communes
├── unit/                          # Tests unitaires (fonctions isolées)
│   └── loaders/
│       └── test_bordereau_validation.py
└── integration/                   # Tests d'intégration (workflow complets)
    ├── test_policy_lifecycle.py   # Tests du cycle de vie des polices (expiration)
    └── test_exclusion_mechanism.py # Tests du mécanisme d'exclusion
```

---

## 🧪 Tests Unitaires (`tests/unit/`)

Les tests unitaires testent des **fonctions ou classes individuelles** de manière isolée.

### `loaders/test_bordereau_validation.py`

**Objectif:** Valider le chargement et la validation des bordereaux

**Ce qui est testé:**
- ✅ Validation de colonnes requises/optionnelles
- ✅ Validation de types de données (numériques, dates)
- ✅ Validation de valeurs nulles
- ✅ Validation de logique métier (inception < expiry)
- ✅ Validation INSURED_NAME en majuscules
- ✅ Gestion des colonnes inconnues
- ✅ Gestion des warnings (expositions à 0, duplicates)

**Modules couverts:**
- `src/loaders/bordereau_validator.py` - **95% de couverture**

**Nombre de tests:** 9

**Comment exécuter:**
```bash
uv run python tests/unit/loaders/test_bordereau_validation.py
```

**Résultat attendu:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    BORDEREAU VALIDATION TEST SUITE                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

TEST 1: Valid Bordereau
✓ Success: Loaded X policies

TEST 2: Bordereau with Warnings
✓ Success: Loaded X policies
Warnings: 2
  - ...

[... 7 autres tests ...]

ALL TESTS COMPLETED
```

---

## 🔗 Tests d'Intégration (`tests/integration/`)

Les tests d'intégration testent des **workflows complets** impliquant plusieurs modules.

### `test_policy_lifecycle.py`

**Objectif:** Tester le cycle de vie des polices et le mécanisme d'expiration

**Ce qui est testé:**
- ✅ Détection des polices expirées à différentes dates de calcul
- ✅ Application de cession = 0 pour polices expirées
- ✅ Statut des polices (actives vs inactives)
- ✅ Raisons d'inactivité dans les résultats

**Modules couverts:**
- `src/engine/policy_lifecycle.py` - 60%
- `src/engine/calculation_engine.py` - partiel
- `src/engine/bordereau_processor.py` - partiel

**Scénarios testés:**
- Police active à la date de calcul
- Police expirée avant la date de calcul
- Police expirant le jour de la date de calcul
- Police dont l'inception est après la date de calcul

**Comment exécuter:**
```bash
uv run python tests/integration/test_policy_lifecycle.py
```

**Résultat attendu:**
```
================================================================================
TEST: Mécanisme de vérification d'expiration des polices
================================================================================

1. Chargement du programme: examples/programs/single_quota_share
   ✓ Programme chargé: Single Quota Share Example

2. Bordereau de test créé:
[... affichage bordereau ...]

================================================================================
Date de calcul: 2024-06-01
================================================================================

Résultats:
--------------------------------------------------------------------------------
✓ COMPANY A        | Expiry: 2025-01-01 | Exposure: 1,000,000 | ...
✓ COMPANY B        | Expiry: 2025-06-01 | Exposure: 2,000,000 | ...
✗ COMPANY C        | Expiry: 2024-01-01 | Exposure:         0 | Status: inactive
  └─ Raison: Policy expired on 2024-01-01...

[... autres dates de calcul ...]
```

---

### `test_exclusion_mechanism.py`

**Objectif:** Tester le mécanisme d'exclusion par dimensions

**Ce qui est testé:**
- ✅ Exclusion de polices par pays (COUNTRY)
- ✅ Exclusion de polices par région (REGION)
- ✅ Matching de conditions avec exclusions
- ✅ Calcul de cession = 0 pour polices exclues
- ✅ Statut d'exclusion dans les résultats

**Modules couverts:**
- `src/engine/condition_matcher.py` - 30%
- `src/engine/policy_lifecycle.py` - partiel
- `src/engine/calculation_engine.py` - partiel

**Scénarios testés:**
- Police matchant une règle d'exclusion
- Police ne matchant pas de règle d'exclusion
- Exclusions multiples dans le programme

**Comment exécuter:**
```bash
uv run python tests/integration/test_exclusion_mechanism.py
```

**Résultat attendu:**
```
================================================================================
TEST DU MÉCANISME D'EXCLUSION
================================================================================

Chargement du programme: examples/programs/quota_share_with_exclusion

[... affichage du programme ...]

Chargement du bordereau: examples/bordereaux/aviation/bordereau_exclusion_test.csv
✓ X polices chargées

================================================================================
RÉSULTATS PAR POLICE:
--------------------------------------------------------------------------------

COMPANY A:
  Exposition originale: 1,000,000
  Exposition effective: 1,000,000
  Statut: included
  ✅ INCLUS - Cession: 250,000 (25%)

COMPANY B (UK):
  Exposition originale: 500,000
  Exposition effective: 0
  Statut: excluded
  ❌ EXCLU - Raison: Matched exclusion rule

[... détails autres polices ...]

================================================================================
RÉSUMÉ
================================================================================

Polices au total: X
  - Incluses: Y
  - Exclues: Z

Exposition totale originale: XXX
Exposition totale effective: YYY
Exposition exclue: ZZZ

Cession totale au réassureur: AAA
```

---

## 🚀 Comment exécuter les tests avec pytest

✅ **Pytest est maintenant installé et configuré !**

### Commandes principales

```bash
# Exécuter tous les tests
uv run pytest

# Exécuter tous les tests avec verbosité
uv run pytest -v

# Exécuter seulement les tests unitaires
uv run pytest tests/unit/

# Exécuter seulement les tests d'intégration
uv run pytest tests/integration/

# Exécuter un fichier de test spécifique
uv run pytest tests/unit/loaders/test_bordereau_validation.py

# Avec couverture de code (génère aussi un rapport HTML)
uv run pytest --cov=src --cov-report=html

# Ouvrir le rapport de couverture
open htmlcov/index.html
```

### Options utiles

```bash
# Afficher les prints pendant les tests
uv run pytest -s

# Arrêter au premier échec
uv run pytest -x

# Exécuter les tests qui ont échoué la dernière fois
uv run pytest --lf

# Mode verbeux avec traceback court
uv run pytest -v --tb=short
```

📖 **Pour plus de détails, consultez [PYTEST_GUIDE.md](PYTEST_GUIDE.md)**

---

## 📊 Couverture actuelle

### Par type de test

| Type | Nombre de tests | Modules couverts |
|------|----------------|------------------|
| **Unitaires** | 9 | 1 module |
| **Intégration** | 2 | ~6 modules |
| **Total** | 11 | ~7 modules |

### Par module

| Module | Couverture | Type de test |
|--------|------------|--------------|
| `loaders/bordereau_validator.py` | ✅ 95% | Unitaire |
| `engine/policy_lifecycle.py` | ⚠️ 60% | Intégration |
| `engine/condition_matcher.py` | ⚠️ 30% | Intégration |
| `engine/calculation_engine.py` | ⚠️ 40% | Intégration |

**Couverture globale estimée: ~20%**

---

## 📝 Conventions

### Nommage des fichiers de test

- Préfixe `test_` obligatoire
- Nom descriptif du module ou de la fonctionnalité testée
- Exemple: `test_bordereau_validation.py`, `test_policy_lifecycle.py`

### Organisation des tests

- **Tests unitaires** (`unit/`) : Organisés selon l'arborescence de `src/`
  - `tests/unit/loaders/` → `src/loaders/`
  - `tests/unit/engine/` → `src/engine/`
  - `tests/unit/domain/` → `src/domain/`

- **Tests d'intégration** (`integration/`) : Nommés selon la fonctionnalité
  - `test_policy_lifecycle.py` : Cycle de vie des polices
  - `test_exclusion_mechanism.py` : Mécanisme d'exclusion
  - `test_full_workflow.py` : Workflow complet (à créer)

### Structure d'un test

```python
def test_[nom_descriptif]():
    """Docstring expliquant ce qui est testé"""
    # Arrange: Préparer les données
    input_data = ...
    expected = ...
    
    # Act: Exécuter la fonction
    result = function(input_data)
    
    # Assert: Vérifier le résultat
    assert result == expected
```

---

## 🎯 Prochaines étapes

1. ✅ Réorganisation des tests existants (fait)
2. ⏳ Installation de pytest
3. ⏳ Ajout de fixtures communes dans `conftest.py`
4. ⏳ Ajout de tests unitaires pour les calculs de base :
   - `tests/unit/domain/products/test_quota_share.py`
   - `tests/unit/domain/products/test_excess_of_loss.py`
   - `tests/unit/engine/test_cession_calculator.py`

---

**Document mis à jour le 13 octobre 2025**

