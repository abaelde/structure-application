# Guide d'utilisation de Pytest

## 🎉 Installation

Pytest est maintenant installé et configuré dans le projet !

```bash
✅ pytest==8.4.2
✅ pytest-cov==7.0.0
```

---

## 🚀 Commandes de base

### Exécuter tous les tests

```bash
uv run pytest
```

### Exécuter avec verbosité

```bash
uv run pytest -v
```

### Exécuter uniquement les tests unitaires

```bash
uv run pytest tests/unit/
```

### Exécuter uniquement les tests d'intégration

```bash
uv run pytest tests/integration/
```

### Exécuter un fichier de test spécifique

```bash
uv run pytest tests/unit/loaders/test_bordereau_validation.py
```

### Exécuter un test spécifique

```bash
uv run pytest tests/unit/loaders/test_bordereau_validation.py::test_valid_bordereau
```

---

## 📊 Couverture de code

### Générer un rapport de couverture dans le terminal

```bash
uv run pytest --cov=src
```

### Générer un rapport HTML détaillé

```bash
uv run pytest --cov=src --cov-report=html
```

Le rapport HTML sera généré dans `htmlcov/index.html`. Ouvrez-le dans un navigateur :

```bash
open htmlcov/index.html
```

### Afficher les lignes manquantes

```bash
uv run pytest --cov=src --cov-report=term-missing
```

### Couverture minimale requise

```bash
uv run pytest --cov=src --cov-fail-under=65
```

Cela fera échouer les tests si la couverture est inférieure à 65%.

---

## 🔍 Options utiles

### Afficher les prints pendant les tests

Par défaut, pytest capture les prints. Pour les afficher :

```bash
uv run pytest -s
```

### Arrêter au premier échec

```bash
uv run pytest -x
```

### Arrêter après N échecs

```bash
uv run pytest --maxfail=3
```

### Exécuter les tests qui ont échoué lors de la dernière exécution

```bash
uv run pytest --lf
```

### Exécuter d'abord les tests qui ont échoué

```bash
uv run pytest --ff
```

### Mode "watch" avec pytest-watch (à installer)

```bash
# Installation
uv add --dev pytest-watch

# Utilisation
uv run ptw
```

---

## 🏷️ Markers (tags de tests)

### Définir des markers

Dans `pyproject.toml`, les markers suivants sont définis :

```toml
markers = [
    "unit: Tests unitaires (fonctions isolées)",
    "integration: Tests d'intégration (workflow complets)",
    "slow: Tests lents",
]
```

### Utiliser un marker

Dans votre test :

```python
import pytest

@pytest.mark.unit
def test_quota_share():
    # ...

@pytest.mark.integration
def test_full_workflow():
    # ...

@pytest.mark.slow
def test_heavy_computation():
    # ...
```

### Exécuter seulement les tests avec un marker

```bash
# Seulement les tests unitaires
uv run pytest -m unit

# Seulement les tests d'intégration
uv run pytest -m integration

# Exclure les tests lents
uv run pytest -m "not slow"
```

---

## 📝 Configuration (pyproject.toml)

La configuration de pytest se trouve dans `pyproject.toml` :

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]              # Où chercher les tests
python_files = "test_*.py"         # Pattern des fichiers de test
python_classes = "Test*"           # Pattern des classes de test
python_functions = "test_*"        # Pattern des fonctions de test
addopts = [
    "-v",                          # Verbeux par défaut
    "--tb=short",                  # Traceback court
    "--strict-markers",            # Erreur si marker inconnu
    "--cov=src",                   # Couverture du dossier src
    "--cov-report=term-missing",   # Afficher lignes manquantes
    "--cov-report=html",           # Générer rapport HTML
]
```

---

## 🧪 État actuel des tests

### Résumé

```
✅ 11 tests passent
📊 65% de couverture de code
```

### Tests par catégorie

| Catégorie | Nombre | Statut |
|-----------|--------|--------|
| **Tests unitaires** | 9 | ✅ Tous passent |
| **Tests d'intégration** | 2 | ✅ Tous passent |

### Détail par fichier

#### Tests unitaires (`tests/unit/`)

**`loaders/test_bordereau_validation.py`** - 9 tests
- ✅ `test_valid_bordereau`
- ✅ `test_bordereau_with_warnings`
- ✅ `test_invalid_bordereau`
- ✅ `test_missing_required_columns`
- ✅ `test_unknown_columns`
- ✅ `test_only_required_columns`
- ✅ `test_partial_dimensions`
- ✅ `test_null_dimension_columns`
- ✅ `test_null_required_columns`

**Couverture:**
- `bordereau_validator.py`: 93% ✅
- `bordereau_loader.py`: 86% ✅

#### Tests d'intégration (`tests/integration/`)

**`test_policy_lifecycle.py`** - 1 test
- ✅ `test_policy_expiry_mechanism`

**Couverture:**
- `policy_lifecycle.py`: 89% ✅
- `calculation_engine.py`: 95% ✅

**`test_exclusion_mechanism.py`** - 1 test
- ✅ `test_exclusion_mechanism`

**Couverture:**
- `condition_matcher.py`: 51% ⚠️
- `structure_orchestrator.py`: 63% ⚠️

---

## 📈 Couverture par module

Modules les mieux couverts :

| Module | Couverture | Statut |
|--------|------------|--------|
| `calculation_engine.py` | 95% | ✅ |
| `bordereau_validator.py` | 93% | ✅ |
| `policy_lifecycle.py` | 89% | ✅ |
| `program_loader.py` | 89% | ✅ |
| `bordereau_loader.py` | 86% | ✅ |
| `exposure_mapping.py` | 100% | ✅ |

Modules nécessitant plus de tests :

| Module | Couverture | Tests manquants |
|--------|------------|-----------------|
| `excess_of_loss.py` | 14% | ❌ Tests unitaires |
| `quota_share.py` | 67% | ❌ Tests unitaires |
| `cession_calculator.py` | 64% | ❌ Tests unitaires |
| `condition_matcher.py` | 51% | ⚠️ Tests unitaires |
| `bordereau_processor.py` | 37% | ⚠️ Tests d'intégration |
| `treaty_manager.py` | 23% | ❌ Tests unitaires |
| `report_display.py` | 9% | ❌ Tests (basse priorité) |

---

## 🛠️ Fixtures communes (conftest.py)

Des fixtures sont disponibles dans `tests/conftest.py` :

```python
import pytest

def test_example(sample_valid_bordereau_data):
    # sample_valid_bordereau_data : DataFrame de bordereau valide
    # ...
```

### Fixtures disponibles

- `sample_bordereau_path`: Chemin vers `bordereau_exemple.csv`
- `sample_valid_bordereau_data`: DataFrame avec données de bordereau valides

### Builders disponibles

Pour créer des programmes de test, utiliser les **builders** au lieu de fichiers Excel :

```python
from tests.builders import build_quota_share, build_program

qs = build_quota_share(name="QS_30", cession_pct=0.30)
program = build_program(name="TEST", structures=[qs])
```

Voir `tests/builders/README.md` pour la documentation complète.

---

## 📋 Exemple de création de test

### Test unitaire simple

```python
# tests/unit/domain/products/test_quota_share.py

import pytest
from src.domain.products import quota_share


def test_quota_share_without_limit():
    """Test quota share sans limite"""
    exposure = 1000.0
    cession_pct = 0.3
    
    result = quota_share(exposure, cession_pct)
    
    assert result == 300.0


def test_quota_share_with_limit_not_reached():
    """Test quota share avec limite non atteinte"""
    exposure = 1000.0
    cession_pct = 0.3
    limit = 500.0
    
    result = quota_share(exposure, cession_pct, limit)
    
    assert result == 300.0  # 30% de 1000 = 300 < 500


def test_quota_share_with_limit_reached():
    """Test quota share avec limite atteinte"""
    exposure = 2000.0
    cession_pct = 0.5
    limit = 500.0
    
    result = quota_share(exposure, cession_pct, limit)
    
    assert result == 500.0  # 50% de 2000 = 1000 > 500, donc capped


def test_quota_share_invalid_cession_rate():
    """Test avec taux de cession invalide"""
    with pytest.raises(ValueError, match="Cession rate must be between 0 and 1"):
        quota_share(1000.0, 1.5)


def test_quota_share_negative_limit():
    """Test avec limite négative"""
    with pytest.raises(ValueError, match="Limit must be positive"):
        quota_share(1000.0, 0.3, limit=-100)
```

### Test d'intégration avec builders

```python
# tests/integration/test_full_workflow.py

import pandas as pd
from src.engine import apply_program_to_bordereau
from tests.builders import build_quota_share, build_program


def test_full_workflow():
    """Test du workflow complet de A à Z"""
    # Arrange - Créer le programme avec les builders
    qs = build_quota_share(name="QS_30", cession_pct=0.30)
    program = build_program(name="TEST", structures=[qs])
    
    # Créer un bordereau de test
    bordereau_df = pd.DataFrame({
        "policy_id": ["POL-001", "POL-002"],
        "INSURED_NAME": ["COMPANY A", "COMPANY B"],
        "exposure": [1_000_000, 2_000_000],
        "INCEPTION_DT": ["2024-01-01", "2024-01-01"],
        "EXPIRE_DT": ["2025-01-01", "2025-01-01"],
        "BUSCL_COUNTRY_CD": ["US", "FR"],
        "BUSCL_LIMIT_CURRENCY_CD": ["USD", "EUR"],
        # ... autres colonnes requises
    })
    
    # Act
    calculation_date = "2024-06-01"
    bordereau_with_cession, results = apply_program_to_bordereau(
        bordereau_df, program, calculation_date=calculation_date
    )
    
    # Assert
    assert len(results) == 2
    assert "cession_to_reinsurer" in results.columns
    assert results["cession_to_reinsurer"].sum() > 0
```

---

## 🎯 Bonnes pratiques

### 1. Nommage des tests

- ✅ `test_quota_share_with_limit_reached`
- ✅ `test_invalid_bordereau_missing_columns`
- ❌ `test1`, `test_func`

### 2. Structure Arrange-Act-Assert

```python
def test_example():
    # Arrange: Préparer les données
    input_data = ...
    expected = ...
    
    # Act: Exécuter la fonction
    result = function(input_data)
    
    # Assert: Vérifier le résultat
    assert result == expected
```

### 3. Un test = une chose testée

- ✅ Un test par scénario
- ❌ Tester plusieurs scénarios dans le même test

### 4. Tests indépendants

- Chaque test doit pouvoir s'exécuter seul
- Pas de dépendance entre tests
- Utiliser des fixtures pour partager du code

### 5. Messages d'assertion clairs

```python
# ✅ Bon
assert result == 300.0, f"Expected 300.0 but got {result}"

# ✅ Encore mieux avec pytest
assert result == 300.0  # pytest montre automatiquement les valeurs
```

---

## 🚦 CI/CD (à venir)

Pour l'intégration continue, ajouter dans `.github/workflows/tests.yml` :

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: uv run pytest --cov=src --cov-fail-under=65
```

---

## 📚 Ressources

- [Documentation officielle de pytest](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Guide des fixtures pytest](https://docs.pytest.org/en/stable/fixture.html)
- [Guide des markers pytest](https://docs.pytest.org/en/stable/example/markers.html)

---

**Document créé le 13 octobre 2025**

