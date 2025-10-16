# Rapport d'Analyse : Problématique de Mapping des Dimensions

## Résumé Exécutif

Le système actuel présente une **fragilité critique** dans le mapping entre les colonnes des bordereaux et les dimensions des programmes de réassurance. Cette fragilité pourrait causer des dysfonctionnements majeurs lors de changements dans le modèle de données des bordereaux.

## Analyse de l'Architecture Actuelle

### 1. Structure des Bordereaux

**Aviation** (`bordereau_aviation_axa_xl.csv`) :
```
POLICY_ID, INSURED_NAME, BUSCL_COUNTRY_CD, BUSCL_REGION, 
BUSCL_CLASS_OF_BUSINESS_1, BUSCL_CLASS_OF_BUSINESS_2, BUSCL_CLASS_OF_BUSINESS_3,
HULL_CURRENCY, LIABILITY_CURRENCY, INDUSTRY, SIC_CODE,
HULL_LIMIT, LIABILITY_LIMIT, HULL_SHARE, LIABILITY_SHARE,
INCEPTION_DT, EXPIRE_DT
```

**Casualty** (`bordereau_casualty_exemple.csv`) :
```
POLICY_ID, INSURED_NAME, BUSCL_COUNTRY_CD, BUSCL_REGION,
BUSCL_CLASS_OF_BUSINESS_1, BUSCL_CLASS_OF_BUSINESS_2, BUSCL_CLASS_OF_BUSINESS_3,
CURRENCY, INDUSTRY, SIC_CODE, LIMIT, CEDENT_SHARE,
INCEPTION_DT, EXPIRE_DT
```

### 2. Structure des Programmes

Les programmes utilisent des **conditions** avec des colonnes nommées différemment :
- `BUSCL_LIMIT_CURRENCY_CD` (dans les programmes)
- vs `HULL_CURRENCY`/`LIABILITY_CURRENCY`/`CURRENCY` (dans les bordereaux)

### 3. Dimensions Utilisées pour le Matching

Dans `src/domain/constants.py`, ligne 28-40 :
```python
DIMENSIONS = [
    "BUSCL_EXCLUDE_CD",
    "BUSCL_ENTITY_NAME_CED",
    "POL_RISK_NAME_CED",
    "BUSCL_COUNTRY_CD",      # ✅ Correspond directement
    "BUSCL_REGION",          # ✅ Correspond directement
    "BUSCL_CLASS_OF_BUSINESS_1",  # ✅ Correspond directement
    "BUSCL_CLASS_OF_BUSINESS_2",  # ✅ Correspond directement
    "BUSCL_CLASS_OF_BUSINESS_3",  # ✅ Correspond directement
    "CURRENCY",              # ⚠️ Problème potentiel
    "HULL_CURRENCY",         # ⚠️ Problème potentiel
    "LIABILITY_CURRENCY",    # ⚠️ Problème potentiel
]
```

## Problèmes Identifiés

### 1. **Mismatch de Noms de Colonnes**

#### Problème Principal : Currency Mapping
- **Programme** : `BUSCL_LIMIT_CURRENCY_CD`
- **Bordereau Aviation** : `HULL_CURRENCY`, `LIABILITY_CURRENCY`
- **Bordereau Casualty** : `CURRENCY`

#### Traitement Actuel (Fragile)
Dans `src/engine/condition_matcher.py`, lignes 64-67 et 98-101 :
```python
# Special handling for currency matching
if dimension == "BUSCL_LIMIT_CURRENCY_CD":
    if not map_currency_condition(condition_value, policy_data, line_of_business):
        matches = False
        break
```

La fonction `map_currency_condition()` fait un mapping hardcodé :
```python
def map_currency_condition(condition_value, policy_data, line_of_business):
    if line_of_business_lower == "aviation":
        hull_currency = policy_data.get("HULL_CURRENCY")
        liability_currency = policy_data.get("LIABILITY_CURRENCY")
        return (hull_currency == condition_value or liability_currency == condition_value)
    elif line_of_business_lower == "casualty":
        currency = policy_data.get("CURRENCY")
        return currency == condition_value
```

### 2. **Mapping Direct et Fragile**

#### Colonnes qui correspondent directement
- `BUSCL_COUNTRY_CD` ↔ `BUSCL_COUNTRY_CD` ✅
- `BUSCL_REGION` ↔ `BUSCL_REGION` ✅
- `BUSCL_CLASS_OF_BUSINESS_1/2/3` ↔ `BUSCL_CLASS_OF_BUSINESS_1/2/3` ✅

#### Colonnes avec mapping spécial
- `BUSCL_LIMIT_CURRENCY_CD` → `HULL_CURRENCY`/`LIABILITY_CURRENCY`/`CURRENCY` ⚠️

### 3. **Problèmes de Robustesse**

#### A. Changement de Noms de Colonnes
Si on change `BUSCL_COUNTRY_CD` en `BustCLCountryCD` dans les bordereaux, le système **ne fonctionnera plus** car :
```python
# Dans condition_matcher.py, ligne 70 et 104
policy_value = policy_data.get(dimension)  # Cherche "BUSCL_COUNTRY_CD"
# Mais le bordereau aura "BustCLCountryCD" → policy_value = None
```

#### B. Ajout de Nouvelles Dimensions
Le système ne gère pas automatiquement de nouvelles dimensions. Il faut :
1. Modifier `DIMENSIONS` dans `constants.py`
2. Potentiellement ajouter du mapping spécial dans `condition_matcher.py`

#### C. Inconsistance dans les Noms
- **Bordereaux** : `INCEPTION_DT`, `EXPIRE_DT`
- **Programmes** : `INCEPTION_DATE`, `EXPIRY_DATE`
- **Constants** : `FIELDS["INCEPTION_DATE"]` = `"INCEPTION_DT"`

## Impact des Changements

### Scénarios de Rupture

1. **Changement de nom de colonne** : `BUSCL_COUNTRY_CD` → `BustCLCountryCD`
   - **Impact** : Toutes les conditions géographiques ne matcheront plus
   - **Symptôme** : Aucune structure ne s'applique

2. **Ajout d'une nouvelle dimension** : `BUSCL_VESSEL_TYPE`
   - **Impact** : Le système ignore complètement cette dimension
   - **Symptôme** : Conditions non respectées silencieusement

3. **Changement de structure de currency** : Fusion de `HULL_CURRENCY` et `LIABILITY_CURRENCY`
   - **Impact** : Le mapping spécial ne fonctionne plus
   - **Symptôme** : Erreurs de matching des devises

## Recommandations Raffinées

### 1. **Mapping Configuration-Driven Flexible**

Créer un système de configuration qui permet de mapper les noms de colonnes entre programmes et bordereaux, avec gestion des dimensions optionnelles :

```python
# Nouveau fichier : src/domain/dimension_mapping.py

# Mapping des noms de colonnes : Programme → Bordereau
DIMENSION_COLUMN_MAPPING = {
    # Dimensions universelles (même nom dans tous les cas)
    "BUSCL_COUNTRY_CD": "BUSCL_COUNTRY_CD",
    "BUSCL_REGION": "BUSCL_REGION", 
    "BUSCL_CLASS_OF_BUSINESS_1": "BUSCL_CLASS_OF_BUSINESS_1",
    "BUSCL_CLASS_OF_BUSINESS_2": "BUSCL_CLASS_OF_BUSINESS_2",
    "BUSCL_CLASS_OF_BUSINESS_3": "BUSCL_CLASS_OF_BUSINESS_3",
    
    # Dimension spéciale : currency (un seul concept, mais noms différents)
    "BUSCL_LIMIT_CURRENCY_CD": {
        "aviation": "HULL_CURRENCY",  # Aviation : on prend HULL_CURRENCY (HULL et LIABILITY doivent être identiques)
        "casualty": "CURRENCY"  # Casualty : 1 seule colonne
    }
}

# Dimensions optionnelles (peuvent être absentes du bordereau)
OPTIONAL_DIMENSIONS = {
    "BUSCL_ENTITY_NAME_CED",
    "POL_RISK_NAME_CED", 
    "BUSCL_EXCLUDE_CD"
}

# Toutes les dimensions sont optionnelles - si absentes, on applique le régime par défaut
# Pas de REQUIRED_DIMENSIONS car cela serait trop limitatif pour les bordereaux
```

### 2. **Mapping Générique avec Gestion des Dimensions Optionnelles**

```python
def get_policy_value(policy_data, dimension, line_of_business=None):
    """
    Récupère la valeur d'une dimension depuis les données de police.
    Gère les dimensions optionnelles et les mappings spéciaux.
    
    Args:
        policy_data: Données de la police depuis le bordereau
        dimension: Nom de la dimension dans le programme (ex: "BUSCL_LIMIT_CURRENCY_CD")
        line_of_business: Type de ligne de business ("aviation" ou "casualty")
    
    Returns:
        Valeur de la dimension ou None si non trouvée/optionnelle
    """
    
    # 1. Mapping direct (cas le plus simple)
    if dimension in DIMENSION_COLUMN_MAPPING:
        mapping = DIMENSION_COLUMN_MAPPING[dimension]
        
        # Mapping simple (string)
        if isinstance(mapping, str):
            return policy_data.get(mapping)
        
        # Mapping complexe (dict avec line_of_business)
        if isinstance(mapping, dict):
            if line_of_business in mapping:
                candidate = mapping[line_of_business]
                if isinstance(candidate, str):
                    return policy_data.get(candidate)
    
    # 2. Fallback : essayer le nom direct
    return policy_data.get(dimension)

def is_dimension_optional(dimension):
    """Toutes les dimensions sont optionnelles - retourne toujours True"""
    return True
```

### 3. **Validation Flexible au Chargement**

```python
def validate_program_bordereau_compatibility(program_dimensions, bordereau_columns, line_of_business):
    """
    Valide la compatibilité entre programme et bordereau.
    Toutes les dimensions sont optionnelles - si absentes, on applique le régime par défaut.
    """
    warnings = []
    errors = []  # Toujours vide - pas de dimensions obligatoires
    
    for dimension in program_dimensions:
        # Avertissement informatif si dimension non trouvée
        if not can_map_dimension(dimension, bordereau_columns, line_of_business):
            warnings.append(f"Dimension '{dimension}' non trouvée dans le bordereau - régime par défaut appliqué")
    
    return errors, warnings

def can_map_dimension(dimension, bordereau_columns, line_of_business):
    """Vérifie si une dimension peut être mappée depuis les colonnes du bordereau"""
    if dimension in DIMENSION_COLUMN_MAPPING:
        mapping = DIMENSION_COLUMN_MAPPING[dimension]
        
        if isinstance(mapping, str):
            return mapping in bordereau_columns
        elif isinstance(mapping, dict):
            if line_of_business in mapping:
                candidate = mapping[line_of_business]
                if isinstance(candidate, str):
                    return candidate in bordereau_columns
    
    # Fallback : nom direct
    return dimension in bordereau_columns

def validate_aviation_currency_consistency(bordereau_columns, line_of_business):
    """
    Validation spécifique pour l'aviation : HULL_CURRENCY et LIABILITY_CURRENCY doivent être identiques.
    """
    if line_of_business != "aviation":
        return []
    
    warnings = []
    
    # Vérifier si les deux colonnes sont présentes
    has_hull = "HULL_CURRENCY" in bordereau_columns
    has_liability = "LIABILITY_CURRENCY" in bordereau_columns
    
    if has_hull and has_liability:
        warnings.append("⚠️  Aviation : Vérifiez que HULL_CURRENCY et LIABILITY_CURRENCY sont identiques dans vos données")
        warnings.append("   Si elles diffèrent, le système prendra HULL_CURRENCY par défaut")
    
    return warnings
```

### 4. **Intégration dans le Condition Matcher**

Modifier `condition_matcher.py` pour utiliser le nouveau système de mapping :

```python
# Remplacer les lignes 70 et 104 dans condition_matcher.py
# AVANT (fragile) :
policy_value = policy_data.get(dimension)

# APRÈS (robuste) :
policy_value = get_policy_value(policy_data, dimension, line_of_business)
```

### 5. **Facilité de Maintenance**

Avec ce système, changer les noms de colonnes devient trivial :

**Exemple :** Si on change `BUSCL_COUNTRY_CD` en `BustCLCountryCD` dans la base de données :

```python
# Dans dimension_mapping.py, modifier une seule ligne :
DIMENSION_COLUMN_MAPPING = {
    "BUSCL_COUNTRY_CD": "BustCLCountryCD",  # Changement ici
    # ... reste inchangé
}
```

**Avantages :**
- ✅ Un seul endroit à modifier
- ✅ Pas de code hardcodé à chercher
- ✅ Validation automatique des mappings
- ✅ Support des dimensions optionnelles

### 6. **Tests de Régression**

Créer des tests qui vérifient la robustesse du mapping :

```python
def test_dimension_mapping_flexibility():
    """Test que le système gère les variations de noms de colonnes"""
    
    # Test avec noms standards
    policy_data_standard = {"BUSCL_COUNTRY_CD": "France", "CURRENCY": "EUR"}
    assert get_policy_value(policy_data_standard, "BUSCL_COUNTRY_CD") == "France"
    
    # Test avec noms modifiés (après changement en base)
    policy_data_modified = {"BustCLCountryCD": "France", "CURRENCY": "EUR"}
    # Mettre à jour le mapping et tester
    # assert get_policy_value(policy_data_modified, "BUSCL_COUNTRY_CD") == "France"

def test_all_dimensions_optional():
    """Test que toutes les dimensions sont optionnelles et appliquent le régime par défaut"""
    
    # Bordereau minimal sans dimensions spécifiques
    policy_data_minimal = {"POLICY_ID": "TEST-001", "CURRENCY": "EUR"}
    
    # Toutes les dimensions doivent retourner None sans planter
    assert get_policy_value(policy_data_minimal, "BUSCL_COUNTRY_CD") is None
    assert get_policy_value(policy_data_minimal, "BUSCL_ENTITY_NAME_CED") is None
    assert get_policy_value(policy_data_minimal, "BUSCL_LIMIT_CURRENCY_CD", "casualty") == "EUR"  # Seule celle présente

def test_currency_mapping_by_line_of_business():
    """Test le mapping simplifié des devises par ligne de business"""
    
    # Aviation - prend HULL_CURRENCY (HULL et LIABILITY doivent être identiques)
    policy_aviation = {"HULL_CURRENCY": "USD", "LIABILITY_CURRENCY": "USD"}  # Cohérent
    assert get_policy_value(policy_aviation, "BUSCL_LIMIT_CURRENCY_CD", "aviation") == "USD"
    
    # Aviation - cas incohérent (à éviter mais géré)
    policy_aviation_incoherent = {"HULL_CURRENCY": "USD", "LIABILITY_CURRENCY": "EUR"}
    assert get_policy_value(policy_aviation_incoherent, "BUSCL_LIMIT_CURRENCY_CD", "aviation") == "USD"  # Prend HULL
    
    # Casualty  
    policy_casualty = {"CURRENCY": "USD"}
    assert get_policy_value(policy_casualty, "BUSCL_LIMIT_CURRENCY_CD", "casualty") == "USD"

def test_aviation_currency_validation():
    """Test la validation de cohérence des devises en aviation"""
    
    # Bordereau avec les deux colonnes devises
    warnings = validate_aviation_currency_consistency(["HULL_CURRENCY", "LIABILITY_CURRENCY"], "aviation")
    assert len(warnings) > 0  # Doit générer un avertissement
    
    # Bordereau casualty (pas d'avertissement)
    warnings = validate_aviation_currency_consistency(["CURRENCY"], "casualty")
    assert len(warnings) == 0
```

## Conclusion Raffinée

Le système proposé est **flexible** et **non-limitant**. Il permet de :

1. **Toutes les dimensions sont optionnelles** : Si absentes, le régime par défaut s'applique
2. **Pas de contraintes sur les bordereaux** : Aucune dimension obligatoire qui limiterait les bordereaux
3. **Mapper facilement les noms** : Un seul endroit pour changer les mappings
4. **Supporter l'évolution** : Ajout facile de nouvelles dimensions ou mappings
5. **Maintenir la robustesse** : Pas d'erreurs, juste des avertissements informatifs

### Priorités d'Implémentation Raffinées

1. **Urgent** : Créer le système de mapping configuration-driven
2. **Important** : Modifier `condition_matcher.py` pour utiliser le nouveau mapping
3. **Souhaitable** : Ajouter la validation informative au chargement
4. **Maintenance** : Créer des tests de régression pour les variations

### Avantages du Plan Raffiné

- ✅ **Aucune dimension obligatoire** : Le système s'adapte à tous les bordereaux
- ✅ **Régime par défaut** : Si une dimension est absente, on applique le régime par défaut
- ✅ **Un seul concept** : Currency reste un seul concept, simplifié (aviation prend HULL_CURRENCY, casualty prend CURRENCY)
- ✅ **Cohérence aviation** : HULL_CURRENCY et LIABILITY_CURRENCY doivent être identiques (validation + avertissement)
- ✅ **Uniformité** : Les pays et régions ont un mapping uniforme
- ✅ **Facilité de maintenance** : Changement de nom en base = modification d'une ligne de configuration
- ✅ **Évolutivité** : Ajout facile de nouvelles dimensions ou mappings
- ✅ **Non-limitant** : Les bordereaux peuvent avoir n'importe quelle structure
