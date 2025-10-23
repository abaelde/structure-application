# Builders - Créer des programmes de test en mémoire

Ce module permet de créer des objets `Program`, `Structure` et `condition` directement en Python, sans passer par des fichiers externes.

## 🎯 Objectif

**Séparer les préoccupations** :
- Tests de **logique métier** → utilisent les builders (rapides, en mémoire)
- Tests de **chargement de fichiers** → utilisent `ProgramManager` (testent l'I/O)

## ⚠️ Validation des conditions spéciales

**IMPORTANT** : Chaque condition spéciale doit avoir **au moins une dimension de matching** pour être valide.

### ✅ Conditions valides
```python
# Avec dimension de matching
{"PRODUCT_TYPE_LEVEL_1": ["Cyber"], "limit": 10_000_000}
{"ORIGINAL_CURRENCY": ["USD"], "cession_pct": 0.25}
{"COUNTRIES": ["US", "CA"], "signed_share": 0.8}
```

### ❌ Conditions invalides
```python
# Sans dimension de matching - REJETÉE
{"limit": 25_000_000}  # ❌ Pas de dimension !

# Avec ancien nom de colonne - REJETÉE  
{"currency_cd": ["USD"], "limit": 10_000_000}  # ❌ Utilisez ORIGINAL_CURRENCY
```

### Dimensions supportées
- `COUNTRIES` - Pays
- `REGION` - Région
- `ORIGINAL_CURRENCY` - Devise originale
- `PRODUCT_TYPE_LEVEL_1/2/3` - Types de produits
- `INCLUDES_HULL` - Inclut hull
- `INCLUDES_LIABILITY` - Inclut liability

## 📦 Modules disponibles

### `condition_builder.py`

```python
from src.builders import build_condition, build_exclusion_condition

# condition simple avec cession 30%
condition = build_condition(cession_pct=0.30)

# condition avec dimensions
condition = build_condition(
    cession_pct=0.25,
    currency_cd="USD",
    country_cd="US",
    region="North America"
)

# condition d'exclusion
exclusion = build_exclusion_condition(
    country_cd="Iran"
)
```

### `structure_builder.py`

```python
from src.builders import build_quota_share, build_excess_of_loss

# Quota Share simple 30%
qs = build_quota_share(
    name="QS_30",
    cession_pct=0.30
)

# Quota Share avec conditions spéciales (par currency)
qs = build_quota_share(
    name="QS_BY_CURRENCY",
    cession_pct=0.30,  # Valeur par défaut
    special_conditions=[
        {"ORIGINAL_CURRENCY": ["USD"], "cession_pct": 0.25},  # Override pour USD
        {"ORIGINAL_CURRENCY": ["EUR"], "cession_pct": 0.35},  # Override pour EUR
    ]
)

# Excess of Loss simple
xl = build_excess_of_loss(
    name="XL_50xs20",
    attachment=20_000_000,
    limit=50_000_000
)

# Excess of Loss avec inuring
xl = build_excess_of_loss(
    name="XL_50xs20",
    attachment=20_000_000,
    limit=50_000_000,
    predecessor_title="QS_30"  # S'applique après QS_30
)
```

### `program_builder.py`

```python
from src.builders import build_program, build_quota_share

# Programme simple avec un QS
qs = build_quota_share(name="QS_30", cession_pct=0.30)
program = build_program(
    name="SINGLE_QS_2024",
    structures=[qs]
)

# Programme avec plusieurs structures en parallèle
qs_10 = build_quota_share(name="QS_10", cession_pct=0.10)
qs_15 = build_quota_share(name="QS_15", cession_pct=0.15)
program = build_program(
    name="DOUBLE_QS_2024",
    structures=[qs_10, qs_15]
)

# Programme avec structures en cascade (inuring)
qs = build_quota_share(name="QS_30", cession_pct=0.30)
xl = build_excess_of_loss(
    name="XL_50xs20",
    attachment=20_000_000,
    limit=50_000_000,
    predecessor_title="QS_30"
)
program = build_program(
    name="QS_THEN_XL",
    structures=[qs, xl]
)
```

## 📝 Exemple complet de test

### Avant (avec fichiers externes)

```python
def test_quota_share():
    program_path = Path("fixtures/programs/single_quota_share")
    if not program_path.exists():
        pytest.skip(f"Programme non trouvé: {program_path}")
    
    manager = ProgramManager()
    program = manager.load(str(program_path))
    
    # ... reste du test
```

**Problèmes** :
- ❌ Nécessite des fichiers externes
- ❌ I/O lent
- ❌ Complexe à maintenir
- ❌ Teste I/O ET logique en même temps

### Après (avec builders)

```python
def test_quota_share():
    """Test application d'un QS 30%"""
    qs = build_quota_share(name="QS_30", cession_pct=0.30)
    program = build_program(name="TEST_QS", structures=[qs])
    
    # ... reste du test
```

**Avantages** :
- ✅ Tout en mémoire
- ✅ Rapide
- ✅ Facile à lire et maintenir
- ✅ Teste uniquement la logique métier

## 🚀 Cas d'usage avancés

### Structure avec exclusions

```python
from tests.builders import build_quota_share, build_exclusion_condition, build_condition

# QS avec exclusions par pays
conditions = [
    build_exclusion_condition(country_cd="Iran"),
    build_exclusion_condition(country_cd="Russia"),
    build_condition(cession_pct=0.25),  # condition catch-all
]

qs = build_quota_share(
    name="QS_WITH_EXCLUSIONS",
    conditions_config=[s.to_dict() for s in conditions]
)
```

### Programme complexe multi-structures

```python
# QS 1 pour USD
qs_usd = build_quota_share(
    name="QS_USD",
    conditions_config=[
        {"currency_cd": "USD", "cession_pct": 0.30}
    ]
)

# QS 2 pour EUR
qs_eur = build_quota_share(
    name="QS_EUR",
    conditions_config=[
        {"currency_cd": "EUR", "cession_pct": 0.40}
    ]
)

# XL qui s'applique après les deux QS
xl = build_excess_of_loss(
    name="XL_100xs50",
    attachment=50_000_000,
    limit=100_000_000,
    predecessor_title="QS_USD"  # Note: gère un seul predecessor
)

program = build_program(
    name="COMPLEX_PROGRAM",
    structures=[qs_usd, qs_eur, xl]
)
```

## 📂 Quand utili

### Utiliser les **builders** pour :
- ✅ Tests d'intégration de la logique métier
- ✅ Tests unitaires des engines
- ✅ Tests de calculs de cession
- ✅ Tests rapides et itératifs

### Utiliser **fichiers externes** pour :
- ✅ Tests du `ProgramManager`
- ✅ Tests de validation du format CSV
- ✅ Tests de colonnes et mappings
- ✅ Programmes de démo/exemples réels

## 🔄 Migration des tests existants

Pour migrer un test existant :

1. **Identifier** la structure du programme dans les fichiers externes
2. **Recréer** avec les builders
3. **Supprimer** les lignes de chargement de fichiers
4. **Vérifier** que le test passe

Exemple de migration :

```diff
- from src.managers import ProgramManager
+ from src.builders import build_quota_share, build_program

  def test_simple_qs():
-     program_path = Path("fixtures/programs/single_quota_share")
-     if not program_path.exists():
-         pytest.skip(f"Programme non trouvé: {program_path}")
-     manager = ProgramManager()
-     program = manager.load(str(program_path))
+     qs = build_quota_share(name="QS_30", cession_pct=0.30)
+     program = build_program(name="TEST_QS", structures=[qs])
      
      # ... reste du test inchangé
```

## 📊 Performance

**Benchmark indicatif** (sur un MacBook Pro M1) :
- Création programme via fichiers : ~50-100ms
- Création programme via builders : ~0.5-1ms

**→ 100x plus rapide !**

## 🧪 Tests des builders eux-mêmes

Les builders sont testés implicitement par les tests d'intégration qui les utilisent. Pas besoin de tests unitaires séparés pour les builders.

## 📚 Ressources

- Guide de test : `tests/README.md`
- Guide Pytest : `tests/PYTEST_GUIDE.md`
- Modèles de domaine : `src/domain/models.py`
- Constantes : `src/domain/constants.py`

