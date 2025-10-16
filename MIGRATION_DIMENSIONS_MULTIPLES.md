# Migration du Data Model : Support des Valeurs Multiples dans les Dimensions

## Contexte et Problématique

### Situation Actuelle
Actuellement, le data model des conditions ne supporte qu'une seule valeur par dimension. Chaque attribut de condition (comme `BUSCL_COUNTRY_CD`, `BUSCL_REGION`, `BUSCL_LIMIT_CURRENCY_CD`, etc.) ne peut contenir qu'une seule valeur.

**Exemple actuel :**
```python
# Une condition ne peut spécifier qu'un seul pays
condition = build_condition(
    country_cd="FR",  # Seulement France
    cession_pct=0.30
)
```

### Problème Identifié
Dans l'interface utilisateur, il est possible de sélectionner plusieurs valeurs pour une même dimension (ex: France ET Allemagne). Avec le système actuel, cela nécessiterait de créer plusieurs lignes de conditions :

```python
# Approche actuelle problématique
conditions = [
    build_condition(country_cd="FR", cession_pct=0.30),
    build_condition(country_cd="DE", cession_pct=0.30),
    # ... pour chaque combinaison
]
```

Cette approche crée une explosion combinatoire du nombre de lignes quand plusieurs dimensions ont plusieurs valeurs.

### Solution Proposée
Implémenter un système de valeurs multiples avec une distinction claire entre :
- **Représentation en mémoire (code)** : Utiliser des listes Python
- **Représentation en stockage (Excel/Base)** : Utiliser des séparateurs (point-virgule `;`)

**Exemple cible :**
```python
# Nouvelle approche avec valeurs multiples (en mémoire)
condition = build_condition(
    country_cd=["FR", "DE"],  # Liste Python - France ET Allemagne
    cession_pct=0.30
)

# En stockage Excel, cela devient : "FR;DE"
```

## Analyse du Data Model Actuel

### Structure des Conditions
D'après l'analyse du code, une condition (`src/domain/models.py`) contient :

**Attributs principaux :**
- `cession_pct` : Pourcentage de cession (Quota Share)
- `attachment` : Point d'attachement (Excess of Loss)
- `limit` : Limite (Excess of Loss)
- `signed_share` : Part du réassureur
- `includes_hull` : Inclut la couverture Hull (Aviation)
- `includes_liability` : Inclut la couverture Liability (Aviation)

**Dimensions de matching (src/domain/constants.py) :**
```python
DIMENSIONS = [
    "BUSCL_EXCLUDE_CD",
    "BUSCL_ENTITY_NAME_CED", 
    "POL_RISK_NAME_CED",
    "BUSCL_COUNTRY_CD",
    "BUSCL_REGION",
    "BUSCL_CLASS_OF_BUSINESS_1",
    "BUSCL_CLASS_OF_BUSINESS_2", 
    "BUSCL_CLASS_OF_BUSINESS_3",
    "CURRENCY",
    "HULL_CURRENCY",
    "LIABILITY_CURRENCY",
]
```

### Builders Actuels
Les builders dans `tests/builders/` permettent de créer des conditions avec une seule valeur par dimension :

```python
# condition_builder.py
def build_condition(
    country_cd: Optional[str] = None,  # Une seule valeur
    region: Optional[str] = None,      # Une seule valeur
    currency_cd: Optional[str] = None, # Une seule valeur
    # ...
) -> condition:
```

### Loaders et Excel
Le système de chargement depuis Excel (`examples/program_creation/excel_utils.py`) lit les valeurs directement depuis les cellules Excel sans traitement de séparateurs.

## Exigences de Migration

### 1. Support des Valeurs Multiples
- **En mémoire** : Modifier le data model pour stocker des listes dans les dimensions
- **En stockage** : Utiliser le point-virgule (`;`) comme séparateur dans Excel/Base
- Maintenir la compatibilité avec les valeurs uniques existantes

### 2. Logique de Matching
- Modifier le système de matching pour vérifier si la valeur de la police correspond à l'une des valeurs de la liste
- Exemple : si condition.country_cd = ["FR", "DE"] et police.country_cd = "FR", alors match

### 3. Interface Builders
- Modifier les builders pour accepter des listes Python
- Maintenir la compatibilité avec l'API existante (valeurs uniques → listes à un élément)

### 4. Chargement Excel
- Modifier les loaders pour convertir les séparateurs en listes Python
- Gérer les cas où Excel contient déjà des séparateurs

### 5. Génération Excel
- Modifier la génération Excel pour convertir les listes Python en séparateurs
- Assurer la lisibilité dans Excel

## Impact sur les Composants

### Composants à Modifier

1. **Data Model (`src/domain/models.py`)**
   - Modifier la classe `condition` pour stocker des listes dans les dimensions
   - Ajouter des méthodes utilitaires pour traiter les listes
   - Modifier la logique de matching pour comparer avec des listes

2. **Builders (`tests/builders/`)**
   - `condition_builder.py` : Accepter des listes Python
   - `structure_builder.py` : Transmettre les listes
   - `program_builder.py` : Pas de changement direct

3. **Loaders (`src/loaders/`)**
   - `program_loader.py` : Convertir les séparateurs Excel en listes Python
   - Autres loaders selon leur usage des dimensions

4. **Excel Utils (`examples/program_creation/excel_utils.py`)**
   - `program_to_excel()` : Convertir les listes Python en séparateurs Excel
   - Gestion de la lisibilité dans Excel

5. **Moteur de Calcul (`src/engine/`)**
   - `condition_matcher.py` : Logique de matching avec listes
   - Autres composants utilisant le matching

### Composants Non Impactés

1. **Tests d'Intégration** : Devraient continuer à fonctionner avec les valeurs uniques
2. **Interface Streamlit** : Pas d'impact direct sur l'affichage
3. **Rapports** : L'affichage des conditions devra être adapté

## Plan de Migration

### Phase 1 : Préparation
1. Créer des tests pour valider le comportement avec valeurs multiples
2. Documenter les cas d'usage et exemples
3. Définir la syntaxe exacte des séparateurs

### Phase 2 : **LOADER EXCEL UNIQUEMENT** (Approche Progressive)
**Objectif** : Permettre l'utilisation de valeurs multiples dans Excel sans modifier la logique de calcul sous-jacente.

**Principe** : Le loader va "déplier" les valeurs multiples en créant plusieurs conditions individuelles en mémoire, gardant ainsi la compatibilité totale avec le système existant.

#### 2.1 Modification du ProgramLoader
1. **Détection des séparateurs** : Identifier les cellules Excel contenant des séparateurs (`;`)
2. **Expansion des conditions** : Créer une condition séparée pour chaque valeur
3. **Préservation de la logique** : Les objets `Condition` en mémoire restent identiques

#### 2.2 Exemple de Transformation
```python
# Excel (une seule ligne)
| BUSCL_COUNTRY_CD | CESSION_PCT | SIGNED_SHARE_PCT |
|------------------|-------------|------------------|
| FR;DE;IT         | 0.30        | 0.25             |

# Mémoire (trois conditions séparées)
condition1 = Condition({"BUSCL_COUNTRY_CD": "FR", "CESSION_PCT": 0.30, "SIGNED_SHARE_PCT": 0.25})
condition2 = Condition({"BUSCL_COUNTRY_CD": "DE", "CESSION_PCT": 0.30, "SIGNED_SHARE_PCT": 0.25})
condition3 = Condition({"BUSCL_COUNTRY_CD": "IT", "CESSION_PCT": 0.30, "SIGNED_SHARE_PCT": 0.25})
```

#### 2.3 Avantages de cette Approche
- **Zéro impact** sur la logique de calcul existante
- **Compatibilité totale** avec tous les tests existants
- **Migration progressive** : on peut tester Excel par Excel
- **Rollback facile** : pas de changement dans le code métier

#### 2.4 Implémentation Détaillée

##### Modification du ProgramLoader
```python
class ProgramLoader:
    def _load_from_file(self):
        program_df = pd.read_excel(self.source, sheet_name=SHEETS.PROGRAM)
        structures_df = pd.read_excel(self.source, sheet_name=SHEETS.STRUCTURES)
        conditions_df = pd.read_excel(self.source, sheet_name=SHEETS.conditions)
        
        program_uw_dept = convert_pandas_to_native(
            program_df.iloc[0].get(PROGRAM_COLS.UNDERWRITING_DEPARTMENT)
        )
        
        conditions_df = self._process_boolean_columns(conditions_df, program_uw_dept)
        
        # NOUVELLE ÉTAPE : Expansion des valeurs multiples
        conditions_df = self._expand_multiple_values(conditions_df)
        
        return program_df, structures_df, conditions_df
    
    def _expand_multiple_values(self, conditions_df: pd.DataFrame) -> pd.DataFrame:
        """Déplie les valeurs multiples en créant plusieurs lignes"""
        expanded_rows = []
        
        for _, row in conditions_df.iterrows():
            # Détecter les colonnes avec des séparateurs
            multiple_value_columns = {}
            single_value_columns = {}
            
            for col in DIMENSIONS:
                if col in row.index:
                    value = row[col]
                    if pd.notna(value) and isinstance(value, str) and ";" in value:
                        # Valeur multiple détectée
                        multiple_value_columns[col] = [v.strip() for v in value.split(";") if v.strip()]
                    else:
                        # Valeur simple
                        single_value_columns[col] = value
            
            # Si aucune valeur multiple, garder la ligne telle quelle
            if not multiple_value_columns:
                expanded_rows.append(row.to_dict())
                continue
            
            # Créer une ligne pour chaque combinaison de valeurs multiples
            # Pour l'instant, on ne gère qu'une seule colonne multiple à la fois
            # (pour éviter l'explosion combinatoire)
            for col, values in multiple_value_columns.items():
                for value in values:
                    new_row = single_value_columns.copy()
                    new_row[col] = value
                    # Ajouter les autres colonnes non-dimension
                    for other_col in row.index:
                        if other_col not in DIMENSIONS:
                            new_row[other_col] = row[other_col]
                    expanded_rows.append(new_row)
        
        return pd.DataFrame(expanded_rows)
```

##### Gestion des Cas Complexes
```python
def _expand_multiple_values_advanced(self, conditions_df: pd.DataFrame) -> pd.DataFrame:
    """Version avancée gérant plusieurs colonnes multiples simultanément"""
    expanded_rows = []
    
    for _, row in conditions_df.iterrows():
        # Analyser toutes les colonnes dimensions
        dimension_values = {}
        non_dimension_values = {}
        
        for col in row.index:
            if col in DIMENSIONS:
                value = row[col]
                if pd.notna(value) and isinstance(value, str) and ";" in value:
                    dimension_values[col] = [v.strip() for v in value.split(";") if v.strip()]
                else:
                    dimension_values[col] = [value] if pd.notna(value) else []
            else:
                non_dimension_values[col] = row[col]
        
        # Générer toutes les combinaisons
        import itertools
        
        # Créer les listes de valeurs pour chaque dimension
        dimension_lists = []
        dimension_names = []
        for col, values in dimension_values.items():
            if values:  # Seulement les dimensions avec des valeurs
                dimension_lists.append(values)
                dimension_names.append(col)
        
        # Générer le produit cartésien
        if dimension_lists:
            for combination in itertools.product(*dimension_lists):
                new_row = non_dimension_values.copy()
                for i, col in enumerate(dimension_names):
                    new_row[col] = combination[i]
                expanded_rows.append(new_row)
        else:
            # Aucune dimension multiple, garder la ligne originale
            expanded_rows.append(row.to_dict())
    
    return pd.DataFrame(expanded_rows)
```


##### Configuration et Paramètres
```python
# Dans constants.py
SEPARATOR = ";"  # Séparateur pour les valeurs multiples
MAX_EXPANSION_LIMIT = 100  # Limite de sécurité pour éviter l'explosion

# Options de configuration
class MultipleValuesConfig:
    ENABLE_MULTIPLE_VALUES = True
    SEPARATOR = ";"
    MAX_VALUES_PER_DIMENSION = 10
    MAX_TOTAL_EXPANSIONS = 100
    WARN_ON_LARGE_EXPANSION = True
```

### Phase 3 : Data Model (Optionnel - Plus Tard)
1. Modifier la classe `condition` pour stocker des listes dans les dimensions
2. Ajouter des méthodes utilitaires (`contains_value()`, `get_values()`)
3. Modifier la logique de matching pour comparer avec des listes

### Phase 4 : Builders (Optionnel - Plus Tard)
1. Modifier `condition_builder.py` pour accepter des listes Python
2. Adapter `structure_builder.py` si nécessaire
3. Mettre à jour les tests des builders

### Phase 5 : Moteur de Calcul (Optionnel - Plus Tard)
1. Modifier `condition_matcher.py` pour comparer avec des listes
2. Vérifier les autres composants du moteur
3. Tests d'intégration complets

### Phase 6 : Validation
1. Tests de régression sur tous les programmes existants
2. Validation avec des cas d'usage réels
3. Documentation utilisateur

## Exemples de Migration

### Avant (Valeurs Uniques)
```python
# Création de plusieurs conditions pour plusieurs pays
qs = build_quota_share(
    name="QS_EUROPE",
    conditions_config=[
        {"country_cd": "FR", "cession_pct": 0.30},
        {"country_cd": "DE", "cession_pct": 0.30},
        {"country_cd": "IT", "cession_pct": 0.30},
    ]
)
```

### Après (Valeurs Multiples)
```python
# Une seule condition pour plusieurs pays (représentation en mémoire)
qs = build_quota_share(
    name="QS_EUROPE",
    conditions_config=[
        {"country_cd": ["FR", "DE", "IT"], "cession_pct": 0.30}
    ]
)
```

### Excel (Représentation en stockage)
```
| BUSCL_COUNTRY_CD | CESSION_PCT |
|------------------|-------------|
| FR;DE;IT         | 0.30        |
```

### Conversion Automatique
- **Chargement Excel → Mémoire** : `"FR;DE;IT"` → `["FR", "DE", "IT"]`
- **Mémoire → Excel** : `["FR", "DE", "IT"]` → `"FR;DE;IT"`

## Architecture Détaillée

### 1. Data Model en Mémoire

#### Structure de la Classe `condition`
```python
class condition:
    def __init__(self, data: Dict[str, Any]):
        # Dimensions stockées comme listes
        self.country_cd = self._normalize_to_list(data.get("BUSCL_COUNTRY_CD"))
        self.region = self._normalize_to_list(data.get("BUSCL_REGION"))
        self.currency_cd = self._normalize_to_list(data.get("BUSCL_LIMIT_CURRENCY_CD"))
        # ... autres dimensions
        
    def _normalize_to_list(self, value):
        """Convertit une valeur en liste, gère la compatibilité descendante"""
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str) and ";" in value:
            return [v.strip() for v in value.split(";")]
        return [value]  # Valeur unique → liste à un élément
    
    def contains_value(self, dimension: str, value: str) -> bool:
        """Vérifie si une dimension contient une valeur spécifique"""
        dimension_values = getattr(self, dimension, [])
        return value in dimension_values
```

#### Avantages de cette Approche
- **Compatibilité descendante** : Les valeurs uniques sont automatiquement converties en listes
- **API naturelle** : `condition.country_cd` retourne une liste, facile à manipuler
- **Matching simple** : `value in condition.country_cd` fonctionne directement

### 2. Interface des Builders

#### API des Builders
```python
# Support des deux formats pour la compatibilité
def build_condition(
    country_cd: Union[str, List[str], None] = None,
    region: Union[str, List[str], None] = None,
    currency_cd: Union[str, List[str], None] = None,
    # ...
) -> condition:
    """Build a condition with support for multiple values per dimension"""
    
    # Normalisation automatique
    condition_data = {
        "BUSCL_COUNTRY_CD": country_cd,
        "BUSCL_REGION": region,
        "BUSCL_LIMIT_CURRENCY_CD": currency_cd,
        # ...
    }
    
    return condition(condition_data)

# Exemples d'utilisation
condition1 = build_condition(country_cd="FR")  # Compatible
condition2 = build_condition(country_cd=["FR", "DE"])  # Nouveau
condition3 = build_condition(country_cd="FR;DE")  # Supporté aussi
```

#### Structure Builder
```python
def build_quota_share(
    name: str,
    conditions_config: Optional[List[Dict[str, Any]]] = None,
    # ...
) -> Structure:
    """Build Quota Share with multiple values support"""
    
    # Exemple de configuration
    conditions_config = [
        {
            "country_cd": ["FR", "DE", "IT"],  # Liste Python
            "region": "EUROPE",
            "cession_pct": 0.30
        }
    ]
```

### 3. Chargement depuis Excel

#### Program Loader
```python
class ProgramLoader:
    def _load_from_file(self):
        # Chargement normal des DataFrames
        conditions_df = pd.read_excel(self.source, sheet_name=SHEETS.conditions)
        
        # Conversion des séparateurs en listes
        conditions_df = self._convert_separators_to_lists(conditions_df)
        
        return program_df, structures_df, conditions_df
    
    def _convert_separators_to_lists(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convertit les séparateurs Excel en listes Python"""
        dimension_columns = [col for col in DIMENSIONS if col in df.columns]
        
        for col in dimension_columns:
            df[col] = df[col].apply(self._parse_dimension_value)
        
        return df
    
    def _parse_dimension_value(self, value):
        """Parse une valeur de dimension (string avec séparateurs → liste)"""
        if pd.isna(value) or value is None:
            return []
        if isinstance(value, str) and ";" in value:
            return [v.strip() for v in value.split(";") if v.strip()]
        return [value] if value else []
```

### 4. Sauvegarde vers Excel

#### Excel Utils
```python
def program_to_excel(program, output_path: str):
    """Convertit un programme en Excel avec conversion listes → séparateurs"""
    
    # ... création des DataFrames ...
    
    # Conversion des listes en séparateurs pour Excel
    conditions_df = self._convert_lists_to_separators(conditions_df)
    
    # Sauvegarde
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        conditions_df.to_excel(writer, sheet_name=SHEETS.conditions, index=False)
    
    auto_adjust_column_widths(output_path)

def _convert_lists_to_separators(self, df: pd.DataFrame) -> pd.DataFrame:
    """Convertit les listes Python en séparateurs Excel"""
    dimension_columns = [col for col in DIMENSIONS if col in df.columns]
    
    for col in dimension_columns:
        df[col] = df[col].apply(self._format_dimension_value)
    
    return df

def _format_dimension_value(self, value):
    """Formate une valeur de dimension (liste → string avec séparateurs)"""
    if not value or (isinstance(value, list) and len(value) == 0):
        return None
    if isinstance(value, list):
        return ";".join(str(v) for v in value if v)
    return str(value) if value else None
```

### 5. Logique de Matching

#### Condition Matcher
```python
def match_condition(
    policy_data: Dict[str, Any], 
    conditions: List[condition], 
    dimension_columns: List[str], 
    line_of_business: str = None
) -> Optional[condition]:
    """Matching avec support des listes dans les dimensions"""
    
    for condition in conditions:
        if condition.is_exclusion():
            continue
            
        matches = True
        specificity = 0
        
        for dimension in dimension_columns:
            condition_values = condition.get(dimension, [])
            
            if condition_values:  # Si la dimension a des valeurs
                # Récupération de la valeur de la police
                policy_value = get_policy_value(policy_data, dimension, line_of_business)
                
                # Matching : vérifier si la valeur de la police est dans la liste
                if policy_value not in condition_values:
                    matches = False
                    break
                specificity += 1
        
        if matches:
            matched_conditions.append((condition, specificity))
    
    # Retourner la condition la plus spécifique
    if matched_conditions:
        matched_conditions.sort(key=lambda x: x[1], reverse=True)
        return matched_conditions[0][0]
    
    return None
```

### 6. Gestion des Cas Spéciaux

#### Valeurs Vides et Null
```python
def _normalize_to_list(self, value):
    """Gestion robuste des valeurs vides"""
    if value is None or pd.isna(value):
        return []
    if isinstance(value, str):
        if not value.strip():
            return []
        if ";" in value:
            return [v.strip() for v in value.split(";") if v.strip()]
        return [value.strip()]
    if isinstance(value, list):
        return [v for v in value if v is not None and not pd.isna(v)]
    return [value]
```

#### Validation et Erreurs
```python
def _validate_dimension_values(self, dimension: str, values: List[str]):
    """Valide les valeurs d'une dimension"""
    if not values:
        return  # Valeurs vides autorisées (régime par défaut)
    
    # Validation spécifique par dimension
    if dimension == "BUSCL_COUNTRY_CD":
        # Vérifier que les codes pays sont valides
        valid_countries = {"FR", "DE", "IT", "ES", "GB", "US", ...}
        invalid = [v for v in values if v not in valid_countries]
        if invalid:
            raise ValueError(f"Invalid country codes: {invalid}")
    
    # ... autres validations ...
```

### 7. Migration Progressive

#### Phase de Transition
```python
# Support des deux formats pendant la migration
def build_condition(**kwargs):
    """Builder avec support des deux formats"""
    
    # Normalisation des arguments
    normalized_kwargs = {}
    for key, value in kwargs.items():
        if key in DIMENSIONS:
            normalized_kwargs[key] = self._normalize_to_list(value)
        else:
            normalized_kwargs[key] = value
    
    return condition(normalized_kwargs)

# Tests de compatibilité
def test_backward_compatibility():
    """Vérifier que l'ancien code continue de fonctionner"""
    # Ancien format
    condition1 = build_condition(country_cd="FR")
    assert condition1.country_cd == ["FR"]
    
    # Nouveau format
    condition2 = build_condition(country_cd=["FR", "DE"])
    assert condition2.country_cd == ["FR", "DE"]
    
    # Format hybride
    condition3 = build_condition(country_cd="FR;DE")
    assert condition3.country_cd == ["FR", "DE"]
```

## Risques et Mitigation

### Risques Identifiés
1. **Régression** : Casser le comportement existant avec valeurs uniques
2. **Performance** : Impact sur les performances du matching
3. **Complexité** : Augmentation de la complexité du code
4. **Compatibilité** : Problèmes avec les fichiers Excel existants

### Stratégies de Mitigation
1. **Tests de régression** : Suite de tests complète avant/après
2. **Compatibilité descendante** : Support des deux formats pendant la transition
3. **Validation** : Tests avec des programmes réels
4. **Documentation** : Guide de migration pour les utilisateurs

## Prochaines Étapes - Phase 2 (Loader Excel)

### Étapes Immédiates

#### 1. Implémentation du ProgramLoader
1. **Ajouter la méthode `_expand_multiple_values()`** dans `ProgramLoader`
2. **Intégrer l'appel** dans `_load_from_file()` après `_process_boolean_columns()`
3. **Ajouter les constantes** de configuration dans `constants.py`

#### 2. Tests de Validation
1. **Créer des tests unitaires** pour `_expand_multiple_values()`
2. **Tester avec des fichiers Excel réels** contenant des séparateurs
3. **Vérifier la compatibilité** avec les programmes existants

#### 3. Validation avec des Cas Réels
1. **Créer un fichier Excel de test** avec des valeurs multiples
2. **Comparer les résultats** avant/après expansion
3. **Vérifier que les calculs** restent identiques

### Exemple d'Implémentation Concrète

#### Fichier de Test Excel
```excel
# Sheet: conditions
| INSPER_ID_PRE | BUSCL_COUNTRY_CD | BUSCL_REGION | CESSION_PCT | SIGNED_SHARE_PCT |
|---------------|------------------|--------------|-------------|------------------|
| QS_001        | FR;DE;IT         | EUROPE       | 0.30        | 0.25             |
| XS_001        | US               | AMERICAS     | 0.20        | 0.15             |
```

#### Résultat Attendu en Mémoire
```python
# 4 conditions au total :
# - 3 conditions pour QS_001 (FR, DE, IT)
# - 1 condition pour XS_001 (US)
```

#### Code à Implémenter
```python
# Dans src/loaders/program_loader.py
def _expand_multiple_values(self, conditions_df: pd.DataFrame) -> pd.DataFrame:
    """Déplie les valeurs multiples en créant plusieurs lignes"""
    if not self._has_multiple_values(conditions_df):
        return conditions_df
    
    expanded_rows = []
    
    for _, row in conditions_df.iterrows():
        expanded_rows.extend(self._expand_single_row(row))
    
    return pd.DataFrame(expanded_rows)

def _has_multiple_values(self, df: pd.DataFrame) -> bool:
    """Vérifie si le DataFrame contient des valeurs multiples"""
    for col in DIMENSIONS:
        if col in df.columns:
            if df[col].astype(str).str.contains(';', na=False).any():
                return True
    return False

def _expand_single_row(self, row: pd.Series) -> List[Dict[str, Any]]:
    """Déplie une seule ligne avec valeurs multiples"""
    # Implémentation détaillée...
```

### Validation et Tests

#### Test de Régression
```python
def test_backward_compatibility():
    """Vérifier que les fichiers Excel existants fonctionnent toujours"""
    # Charger un programme existant
    loader = ProgramLoader("examples/programs/aviation_axa_xl_2024.xlsx")
    program = loader.get_program()
    
    # Vérifier que le nombre de conditions est identique
    # (pas d'expansion non désirée)
    assert len(program.structures[0].conditions) == expected_count
```

#### Test de Nouvelle Fonctionnalité
```python
def test_multiple_values_expansion():
    """Tester l'expansion des valeurs multiples"""
    # Créer un DataFrame de test
    test_data = pd.DataFrame([{
        "INSPER_ID_PRE": "TEST_001",
        "BUSCL_COUNTRY_CD": "FR;DE;IT",
        "CESSION_PCT": 0.30,
        "SIGNED_SHARE_PCT": 0.25
    }])
    
    # Tester l'expansion
    loader = ProgramLoader("dummy")
    expanded = loader._expand_multiple_values(test_data)
    
    # Vérifications
    assert len(expanded) == 3
    assert expanded["BUSCL_COUNTRY_CD"].tolist() == ["FR", "DE", "IT"]
```

### Risques et Mitigation

#### Risques Identifiés
1. **Performance** : L'expansion peut créer beaucoup de lignes
2. **Mémoire** : Augmentation de la consommation mémoire
3. **Complexité** : Gestion des cas edge (valeurs vides, séparateurs multiples)

#### Stratégies de Mitigation
1. **Limites de sécurité** : Limiter le nombre d'expansions
2. **Logging** : Logger les expansions pour monitoring
3. **Tests exhaustifs** : Couvrir tous les cas edge
4. **Rollback** : Possibilité de désactiver la fonctionnalité

### Configuration

#### Paramètres de Configuration
```python
# Dans src/domain/constants.py
MULTIPLE_VALUES_CONFIG = SimpleNamespace(
    ENABLE_MULTIPLE_VALUES=True,
    SEPARATOR=";",
    MAX_VALUES_PER_DIMENSION=10,
    MAX_TOTAL_EXPANSIONS=100,
    WARN_ON_LARGE_EXPANSION=True,
    LOG_EXPANSIONS=True
)
```

## Prochaines Étapes - Phases Suivantes

1. **Validation du plan** avec l'équipe
2. **Création des tests** pour les nouveaux comportements
3. **Implémentation progressive** selon le plan de migration
4. **Tests et validation** à chaque étape
5. **Documentation** des changements pour les utilisateurs

---

*Document créé le : $(date)*
*Version : 1.0*
*Statut : En cours de validation*
