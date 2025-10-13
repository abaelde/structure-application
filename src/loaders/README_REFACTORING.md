# Refactorisation : Séparation des Responsabilités

## 📋 Vue d'ensemble

La refactorisation a séparé le module `bordereau_loader.py` en deux modules distincts pour respecter le principe de responsabilité unique (Single Responsibility Principle).

## 🔄 Avant / Après

### Avant
```
src/loaders/
└── bordereau_loader.py (315 lignes)
    ├── Chargement des données
    └── Validation des données
```

### Après
```
src/loaders/
├── bordereau_loader.py (62 lignes)
│   └── Responsabilité : CHARGEMENT uniquement
└── bordereau_validator.py (265 lignes)
    └── Responsabilité : VALIDATION uniquement
```

## 📦 Modules

### 1. `bordereau_loader.py`
**Responsabilité** : Chargement des données depuis différentes sources

**Fonctionnalités** :
- Détection automatique du type de fichier (CSV)
- Détection automatique de la ligne métier depuis le path
- Mapping automatique des colonnes d'exposition (via `exposure_mapping.py`)
- Option pour valider ou non lors du chargement

**Classe principale** : `BordereauLoader`

**Exemple d'utilisation** :
```python
from src.loaders import BordereauLoader

# Avec validation (par défaut)
loader = BordereauLoader("path/to/bordereau.csv")
df = loader.load()

# Sans validation
loader = BordereauLoader("path/to/bordereau.csv", validate=False)
df = loader.load()
```

### 2. `bordereau_validator.py`
**Responsabilité** : Validation des données du bordereau

**Validations effectuées** :
- ✅ Bordereau non vide
- ✅ Colonnes requises présentes
- ✅ Pas de colonnes inconnues
- ✅ Pas de valeurs nulles dans les colonnes requises
- ✅ Types de données corrects (numériques, dates)
- ✅ Valeurs numériques valides (pas de négatifs)
- ✅ Noms assurés en majuscules
- ✅ Cohérence de la ligne métier
- ✅ Logique métier (dates inception < expiry)

**Classe principale** : `BordereauValidator`

**Exemple d'utilisation** :
```python
from src.loaders import BordereauValidator

# Valider un DataFrame déjà chargé
validator = BordereauValidator(df, line_of_business="aviation")
validator.validate()

# Accéder aux warnings et erreurs
print(validator.validation_warnings)
print(validator.validation_errors)
```

### 3. Fonction helper `load_bordereau()`
**Commodité** : Charge et valide en une seule étape

```python
from src.loaders import load_bordereau

df = load_bordereau("path/to/bordereau.csv")
```

## ✅ Avantages de la Refactorisation

1. **Séparation des responsabilités** : Chaque module a une responsabilité unique et bien définie
2. **Testabilité améliorée** : Possibilité de tester le chargement et la validation indépendamment
3. **Réutilisabilité** : Possibilité de valider des données sans passer par le loader
4. **Maintenabilité** : Fichiers plus petits et plus faciles à comprendre
5. **Flexibilité** : Option de charger sans valider si nécessaire
6. **Extensibilité** : Facilité d'ajout de nouvelles validations ou sources de données

## 🔄 Rétrocompatibilité

La refactorisation est **100% rétrocompatible** :
- L'API publique reste inchangée
- `BordereauLoader` expose toujours `validation_warnings` et `validation_errors`
- `load_bordereau()` fonctionne exactement comme avant
- Tous les tests existants passent sans modification

## 📚 Exports Publics

Le module `src/loaders` exporte :
```python
from src.loaders import (
    BordereauLoader,        # Classe de chargement
    BordereauValidator,     # Classe de validation
    load_bordereau,         # Fonction helper
    BordereauValidationError,  # Exception
)
```

## 🧪 Tests

Tous les tests passent avec succès :
- ✅ `examples/scripts/test_bordereau_validation.py` : 9/9 tests réussis
- ✅ `main.py` : Exécution complète fonctionnelle
- ✅ Aucune erreur de linter

## 📝 Notes Techniques

### Dépendances entre modules
```
bordereau_loader.py
    ├── Importe: bordereau_validator (BordereauValidator, BordereauValidationError)
    └── Importe: exposure_mapping (find_exposure_column)

bordereau_validator.py
    └── Importe: src.domain (FIELDS)
```

### Workflow de chargement
```
1. BordereauLoader.__init__()
   └── Détecte source_type et line_of_business

2. BordereauLoader.load()
   ├── _load_from_csv()
   │   └── Mappe les colonnes d'exposition
   └── Si validate=True:
       └── BordereauValidator.validate()
           ├── Exécute toutes les validations
           └── Lève BordereauValidationError si erreurs
```

