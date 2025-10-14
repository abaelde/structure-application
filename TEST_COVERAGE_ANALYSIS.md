# Analyse de la Couverture de Tests

## Date d'analyse
13 octobre 2025

## 📊 Vue d'ensemble

### Tests existants identifiés

1. **`test_policy_expiry.py`** (racine)
   - Type: Test d'intégration
   - Statut: ✅ Opérationnel
   
2. **`test_exclusion_mechanism.py`** (racine)
   - Type: Test d'intégration
   - Statut: ✅ Opérationnel

3. **`examples/scripts/test_bordereau_validation.py`**
   - Type: Suite de tests unitaires
   - Statut: ✅ Opérationnel

### Structure du code à tester

```
src/
├── domain/
│   ├── constants.py
│   └── products/
│       ├── quota_share.py          ❌ NON TESTÉ
│       └── excess_of_loss.py       ❌ NON TESTÉ
├── engine/
│   ├── bordereau_processor.py      ⚠️  PARTIELLEMENT TESTÉ
│   ├── calculation_engine.py       ⚠️  PARTIELLEMENT TESTÉ
│   ├── cession_calculator.py       ❌ NON TESTÉ
│   ├── policy_lifecycle.py         ⚠️  PARTIELLEMENT TESTÉ
│   ├── section_matcher.py          ⚠️  PARTIELLEMENT TESTÉ
│   ├── structure_orchestrator.py   ⚠️  PARTIELLEMENT TESTÉ
│   └── treaty_manager.py           ❌ NON TESTÉ
├── loaders/
│   ├── bordereau_loader.py         ❌ NON TESTÉ
│   ├── bordereau_validator.py      ✅ BIEN TESTÉ
│   ├── exposure_mapping.py         ❌ NON TESTÉ
│   └── program_loader.py           ❌ NON TESTÉ
└── presentation/
    ├── program_display.py          ❌ NON TESTÉ
    └── report_display.py           ❌ NON TESTÉ
```

---

## 📝 Analyse détaillée des tests existants

### 1. `test_policy_expiry.py`

**Ce qui est testé:**
- ✅ Mécanisme d'expiration des polices à différentes dates de calcul
- ✅ Statut des polices (actives vs expirées)
- ✅ Impact de l'expiration sur la cession

**Couverture:**
- `policy_lifecycle.py::check_policy_status()` - ✅
- `policy_lifecycle.py::create_inactive_result()` - ✅
- `calculation_engine.py::apply_program()` - ⚠️ (seulement aspect expiration)
- `bordereau_processor.py::apply_program_to_bordereau()` - ⚠️

**Points forts:**
- Test avec dates multiples
- Validation des raisons d'inactivité
- Vérification de la cession = 0 pour polices expirées

**Lacunes:**
- Pas de test avec dates invalides
- Pas de test edge case (date expiry == date calcul)
- Pas de test avec calculation_date = None

---

### 2. `test_exclusion_mechanism.py`

**Ce qui est testé:**
- ✅ Mécanisme d'exclusion par dimensions
- ✅ Matching de sections avec exclusions
- ✅ Calcul de cession avec exclusions

**Couverture:**
- `section_matcher.py::check_exclusion()` - ✅
- `section_matcher.py::match_section()` - ⚠️ (seulement avec exclusions)
- `policy_lifecycle.py::create_excluded_result()` - ✅
- `calculation_engine.py::apply_program()` - ⚠️ (seulement aspect exclusion)

**Points forts:**
- Test avec bordereau réel
- Validation des raisons d'exclusion
- Rapport détaillé avec compteurs

**Lacunes:**
- Pas de test unitaire sur `check_exclusion()` directement
- Pas de test sur exclusions multiples (conflits)
- Pas de test sur exclusions partielles

---

### 3. `examples/scripts/test_bordereau_validation.py`

**Ce qui est testé:**
- ✅ Validation de colonnes requises/optionnelles
- ✅ Validation de types de données
- ✅ Validation de dates
- ✅ Validation de valeurs numériques
- ✅ Validation de logique métier (inception < expiry)
- ✅ Validation INSURED_NAME en majuscules
- ✅ Gestion des colonnes inconnues
- ✅ Gestion des valeurs nulles

**Couverture:**
- `bordereau_validator.py::BordereauValidator` - ✅✅✅ EXCELLENTE
- Toutes les méthodes de validation - ✅

**Points forts:**
- Suite de tests très complète (9 tests)
- Couvre tous les cas d'erreur
- Couvre les warnings (expositions à 0, duplicates)
- Tests positifs et négatifs

**Lacunes:**
- Pas de test sur `bordereau_loader.py` (chargement CSV)
- Pas de test d'intégration bordereau_loader + validator

---

## ❌ Modules NON TESTÉS

### 1. **`src/domain/products/quota_share.py`**

**Priorité: 🔴 CRITIQUE**

Fonctions à tester:
- `quota_share(exposure, cession_PCT, limit=None)`

Scénarios de test manquants:
```python
# Tests unitaires à créer:
- ✗ Quota share sans limite
- ✗ Quota share avec limite
- ✗ Limite atteinte vs non atteinte
- ✗ Cession rate = 0
- ✗ Cession rate = 1
- ✗ Cession rate invalide (< 0, > 1)
- ✗ Limite négative
- ✗ Exposure = 0
- ✗ Exposure négatif
```

---

### 2. **`src/domain/products/excess_of_loss.py`**

**Priorité: 🔴 CRITIQUE**

Fonctions à tester:
- `excess_of_loss(exposure, attachment_point_100, limit_100)`

Scénarios de test manquants:
```python
# Tests unitaires à créer:
- ✗ Exposure < attachment (return 0)
- ✗ Exposure = attachment (return 0)
- ✗ Exposure > attachment mais < attachment + limit
- ✗ Exposure > attachment + limit (capping à limit)
- ✗ Attachment négatif (ValueError)
- ✗ Limit négatif (ValueError)
- ✗ Exposure = 0
- ✗ Edge cases avec valeurs très grandes
```

---

### 3. **`src/engine/cession_calculator.py`**

**Priorité: 🔴 CRITIQUE**

Fonctions à tester:
- `apply_section(exposure, section, type_of_participation)`

Scénarios de test manquants:
```python
# Tests unitaires à créer:
- ✗ Application quota_share sans limite
- ✗ Application quota_share avec limite
- ✗ Application excess_of_loss
- ✗ CESSION_PCT manquant pour quota_share (ValueError)
- ✗ ATTACHMENT/LIMIT manquant pour XL (ValueError)
- ✗ Type de participation inconnu (ValueError)
- ✗ Signed share = 1.0 (default)
- ✗ Signed share = 0.5
- ✗ Signed share = NaN (doit être 1.0)
- ✗ Calcul correct de cession_to_layer vs cession_to_reinsurer
```

---

### 4. **`src/engine/section_matcher.py`**

**Priorité: 🟡 HAUTE**

Actuellement testé indirectement, mais manque de tests unitaires.

Scénarios de test manquants:
```python
# Tests unitaires pour check_exclusion():
- ✗ Exclusion avec 1 dimension
- ✗ Exclusion avec multiples dimensions
- ✗ Exclusion ne match pas
- ✗ Aucune exclusion définie
- ✗ Valeur NaN dans section

# Tests unitaires pour match_section():
- ✗ Match exact avec toutes dimensions
- ✗ Match partiel (section moins spécifique)
- ✗ Plusieurs sections matchent (test spécificité)
- ✗ Aucune section ne match
- ✗ Section avec certaines dimensions NaN
- ✗ Ignorer les sections d'exclusion
```

---

### 5. **`src/engine/structure_orchestrator.py`**

**Priorité: 🟡 HAUTE**

Module complexe avec logique d'inuring. Actuellement testé uniquement en intégration.

Scénarios de test manquants:
```python
# Tests pour process_structures():
- ✗ Structure simple (pas de predecessor)
- ✗ Structure avec predecessor (inuring)
- ✗ Multiple structures en séquence
- ✗ Structure sans section matchée
- ✗ Calcul d'input_exposure depuis predecessor
- ✗ Rescaling QS→XL
- ✗ Pas de rescaling pour QS→QS ou XL→XL
- ✗ Calcul correct de retention_pct
- ✗ Structures_detail pour applied vs unapplied
- ✗ Ordre de processing avec dependencies
- ✗ Dépendance circulaire (si possible)

# Tests helper functions:
- ✗ _calculate_input_exposure()
- ✗ _rescale_section_if_needed()
- ✗ _calculate_retention_pct()
```

---

### 6. **`src/engine/treaty_manager.py`**

**Priorité: 🟠 MOYENNE**

Module important pour multi-year treaties mais moins critique.

Scénarios de test manquants:
```python
# Tests pour TreatyManager:
- ✗ Chargement de multiples traités
- ✗ Sélection risk_attaching (utilise policy inception)
- ✗ Sélection loss_occurring (utilise calculation_date)
- ✗ Traité non trouvé pour une année
- ✗ claim_basis invalide (ValueError)
- ✗ calculation_date = None (utilise date actuelle)
- ✗ get_available_years()
- ✗ get_treaty_for_year()
- ✗ get_treaty_info()
```

---

### 7. **`src/loaders/program_loader.py`**

**Priorité: 🔴 CRITIQUE**

Chargement de programme Excel - crucial pour l'application.

Scénarios de test manquants:
```python
# Tests pour ProgramLoader:
- ✗ Chargement fichier Excel valide
- ✗ Structures avec INSPER_ID_PRE
- ✗ Structures avec BUSINESS_TITLE (fallback)
- ✗ Detection correcte des dimension_columns
- ✗ Parsing de toutes les colonnes de configuration
- ✗ Fichier inexistant (erreur)
- ✗ Fichier corrompu
- ✗ Sheets manquants
- ✗ Colonnes requises manquantes
```

---

### 8. **`src/loaders/bordereau_loader.py`**

**Priorité: 🔴 CRITIQUE**

Le validator est testé, mais pas le loader lui-même.

Scénarios de test manquants:
```python
# Tests pour BordereauLoader:
- ✗ Chargement CSV valide
- ✗ Détection automatique de line_of_business depuis path
- ✗ Mapping des colonnes d'exposure (exposure_mapping)
- ✗ Conversion de types
- ✗ Génération de policy_id si manquant
- ✗ Fichier avec encodage différent
- ✗ Fichier avec séparateur différent (;)
```

---

### 9. **`src/loaders/exposure_mapping.py`**

**Priorité: 🟡 HAUTE**

Fonctions à tester:
- `find_exposure_column(df_columns, line_of_business)`

Scénarios de test manquants:
```python
# Tests unitaires:
- ✗ Aviation avec "hull_limit" trouvé
- ✗ Aviation avec "liab_limit" trouvé
- ✗ Casualty avec "limit" trouvé
- ✗ Test avec "expo"/"exposure"
- ✗ LOB inconnu (retourne None)
- ✗ LOB = None
- ✗ Colonne non trouvée dans le DF
```

---

### 10. **`src/presentation/`**

**Priorité: 🟢 BASSE**

Modules de présentation - tests moins critiques mais utiles.

Modules:
- `program_display.py` - ✗ Aucun test
- `report_display.py` - ✗ Aucun test

Ces modules sont principalement pour l'affichage et sont moins critiques à tester unitairement.

---

## 🎯 Plan de test recommandé

### Phase 1: Tests Unitaires Critiques (Priorité 🔴)

#### 1.1 Domain/Products
- [ ] `test_quota_share.py` - 10 tests
- [ ] `test_excess_of_loss.py` - 10 tests

#### 1.2 Engine Core
- [ ] `test_cession_calculator.py` - 15 tests

#### 1.3 Loaders
- [ ] `test_program_loader.py` - 12 tests
- [ ] `test_bordereau_loader.py` - 10 tests

**Estimation: ~60 tests à créer**

---

### Phase 2: Tests Unitaires Haute Priorité (Priorité 🟡)

#### 2.1 Engine
- [ ] `test_section_matcher.py` - 15 tests
- [ ] `test_structure_orchestrator.py` - 20 tests
- [ ] `test_exposure_mapping.py` - 8 tests

**Estimation: ~45 tests à créer**

---

### Phase 3: Tests Intégration & Moyenne Priorité (Priorité 🟠)

#### 3.1 Engine
- [ ] `test_treaty_manager.py` - 12 tests
- [ ] `test_calculation_engine_integration.py` - 15 tests

#### 3.2 End-to-End
- [ ] `test_full_workflow.py` - 10 tests
  - Chargement programme + bordereau
  - Application complète
  - Vérification résultats

**Estimation: ~37 tests à créer**

---

### Phase 4: Tests Complémentaires (Priorité 🟢)

#### 4.1 Edge Cases
- [ ] `test_edge_cases.py` - 15 tests
  - Valeurs extrêmes
  - Combinaisons rares
  - Performance

#### 4.2 Validation améliorée
- [ ] Amélioration des tests existants
- [ ] Tests de performance/charge

**Estimation: ~20 tests à créer**

---

## 📈 Métriques de couverture actuelle

### Estimation de couverture par module

| Module | Couverture estimée | Priorité |
|--------|-------------------|----------|
| `domain/products/` | 0% | 🔴 |
| `engine/cession_calculator.py` | 0% | 🔴 |
| `engine/section_matcher.py` | 30% (indirect) | 🟡 |
| `engine/structure_orchestrator.py` | 20% (indirect) | 🟡 |
| `engine/policy_lifecycle.py` | 60% | ⚠️ |
| `engine/calculation_engine.py` | 40% (indirect) | ⚠️ |
| `engine/bordereau_processor.py` | 30% (indirect) | ⚠️ |
| `engine/treaty_manager.py` | 0% | 🟠 |
| `loaders/bordereau_validator.py` | 95% | ✅ |
| `loaders/bordereau_loader.py` | 0% | 🔴 |
| `loaders/program_loader.py` | 0% | 🔴 |
| `loaders/exposure_mapping.py` | 0% | 🟡 |
| `presentation/` | 0% | 🟢 |

### Couverture globale estimée: **~20%**

---

## 🔧 Recommandations

### 1. Infrastructure de tests

**Actuellement:** Tests lancés manuellement, pas de framework de test

**À mettre en place:**
```bash
# Ajouter pytest
uv add --dev pytest pytest-cov

# Structure proposée:
tests/
├── unit/
│   ├── domain/
│   │   └── products/
│   ├── engine/
│   └── loaders/
├── integration/
│   ├── test_policy_expiry.py (déplacer)
│   └── test_exclusion_mechanism.py (déplacer)
└── conftest.py (fixtures communes)
```

### 2. Fixtures réutilisables

Créer des fixtures pour:
- Programmes types (QS simple, XL simple, Multi-structures)
- Bordereaux types (valides, avec erreurs)
- Sections types (avec/sans exclusions)
- Dates types (actives, expirées, edge cases)

### 3. Outils de couverture

```bash
# Configuration pytest.ini
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "--cov=src --cov-report=html --cov-report=term-missing"
```

### 4. CI/CD

Mettre en place:
- GitHub Actions pour run tests automatiquement
- Exigence de couverture minimum (ex: 80%)
- Pre-commit hooks pour linting et tests

### 5. Documentation des tests

- Documenter les scénarios de test
- Créer des exemples de tests pour chaque type
- Maintenir ce document à jour

---

## 📋 Template de test proposé

```python
"""
Tests unitaires pour [MODULE]

Couvre:
- [Fonctionnalité 1]
- [Fonctionnalité 2]
"""

import pytest
import pandas as pd
from src.[module] import [fonction]


class Test[Fonction]:
    """Tests pour la fonction [fonction]"""
    
    def test_[scenario_nominal](self):
        """Test du cas nominal"""
        # Arrange
        input_data = ...
        expected = ...
        
        # Act
        result = fonction(input_data)
        
        # Assert
        assert result == expected
    
    def test_[scenario_edge_case](self):
        """Test d'un edge case"""
        # ...
    
    def test_[scenario_erreur](self):
        """Test d'un cas d'erreur"""
        with pytest.raises(ValueError, match="message attendu"):
            fonction(invalid_input)


@pytest.fixture
def sample_data():
    """Fixture pour données de test réutilisables"""
    return {...}
```

---

## 🎯 Objectifs à court terme (1-2 semaines)

1. ✅ Analyse de couverture (ce document)
2. ⏳ Mettre en place pytest et structure de tests
3. ⏳ Phase 1: Tests unitaires critiques
   - quota_share / excess_of_loss
   - cession_calculator
   - program_loader
4. ⏳ Atteindre 50% de couverture

## 🎯 Objectifs à moyen terme (1 mois)

1. ⏳ Phase 2: Tests unitaires haute priorité
2. ⏳ Réorganiser tests existants dans nouvelle structure
3. ⏳ Atteindre 70% de couverture
4. ⏳ Mettre en place CI/CD

## 🎯 Objectifs à long terme (2-3 mois)

1. ⏳ Phases 3-4 complètes
2. ⏳ Atteindre 85%+ de couverture
3. ⏳ Tests de performance
4. ⏳ Documentation complète des tests

---

## 📝 Notes

- Les tests d'intégration actuels (`test_policy_expiry.py`, `test_exclusion_mechanism.py`) sont bien faits mais devraient être complétés par des tests unitaires
- Le `test_bordereau_validation.py` est exemplaire et peut servir de modèle
- Priorité absolue: tester les fonctions de calcul (`quota_share`, `excess_of_loss`, `cession_calculator`) car elles sont au cœur du métier
- Le code est bien structuré, ce qui facilitera l'ajout de tests

---

**Document généré le 13 octobre 2025**

