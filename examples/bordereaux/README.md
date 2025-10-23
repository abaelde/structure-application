# Bordereaux - Data Model et Spécifications

## Vue d'Ensemble

Ce document définit le **data model** des bordereaux utilisés dans le système de réassurance. Un bordereau est un fichier CSV contenant les informations sur les polices d'assurance souscrites, utilisé pour calculer les cessions de réassurance.

## Data Model

### Règles Générales (Applicables à Tous les Bordereaux)

Quel que soit la ligne de business, **tous les bordereaux** doivent respecter les règles suivantes :

#### Colonnes Obligatoires Minimales

| Colonne | Nom Exact | Type | Format | Description | Règles de Validation |
|---------|-----------|------|--------|-------------|----------------------|
| **Insured Name** | `INSURED_NAME` | String | **MAJUSCULES** | Nom de l'assuré | ✅ Obligatoire<br>✅ DOIT être en MAJUSCULES uniquement<br>❌ Erreur si minuscules présentes |
| **Inception Date** | `INCEPTION_DT` | Date | `YYYY-MM-DD` | Date de début de couverture | ✅ Obligatoire<br>✅ Format ISO 8601<br>❌ Erreur si format invalide |
| **Expiry Date** | `EXPIRE_DT` | Date | `YYYY-MM-DD` | Date de fin de couverture | ✅ Obligatoire<br>✅ Format ISO 8601<br>✅ Doit être > `INCEPTION_DT`<br>❌ Erreur si ≤ inception |

#### Colonnes Obligatoires Standard

En plus des colonnes minimales, ces colonnes sont également requises :

| Colonne | Nom Exact | Type | Format | Description | Règles de Validation |
|---------|-----------|------|--------|-------------|----------------------|
| **Exposition** | `exposure` | Numeric | Nombre positif | Montant d'exposure en valeur absolue | ✅ Obligatoire<br>✅ Valeur positive<br>⚠️ Warning si = 0<br>❌ Erreur si < 0 |
| **Line of Business** | `line_of_business` | String | Texte | Ligne de business de la police | ✅ Obligatoire<br>✅ Doit être cohérent avec le dossier |

#### Colonnes Optionnelles Standards

| Colonne | Nom Exact | Type | Description | Utilisation |
|---------|-----------|------|-------------|-------------|
| **Policy ID** | `policy_id` | String | Identifiant unique de la police | Tracking, reporting, traçabilité |

#### Colonnes Dimensionnelles (Optionnelles)

Ces colonnes sont utilisées pour le **matching avancé** des conditions dans les programmes de réassurance :

| Colonne | Nom Exact | Type | Description |
|---------|-----------|------|-------------|
| **Country** | `COUNTRY` | String | Code pays (ISO) |
| **Region** | `REGION` | String | Région géographique |
| **Class of Business 1** | `PRODUCT_TYPE_LEVEL_1` | String | Classe de business niveau 1 |
| **Class of Business 2** | `PRODUCT_TYPE_LEVEL_2` | String | Classe de business niveau 2 |
| **Class of Business 3** | `PRODUCT_TYPE_LEVEL_3` | String | Classe de business niveau 3 |
| **Currency (Aviation)** | `HULL_CURRENCY`, `LIAB_CURRENCY` | String | Code devise Hull/Liability (ISO 4217) |
| **Currency (Casualty)** | `ORIGINAL_CURRENCY` | String | Code devise (ISO 4217) |
| **Industry** | `industry` | String | Secteur industriel |
| **SIC Code** | `sic_code` | String/Numeric | Code SIC (Standard Industrial Classification) |
| **Include** | `include` | String/Boolean | Indicateur d'inclusion/exclusion |

### Règles Spécifiques par Line of Business

#### Aviation

Pour les bordereaux situés dans `bordereaux/aviation/` :

**Colonnes de devises obligatoires** :
- `HULL_CURRENCY` : Devise pour les limites Hull (obligatoire)
- `LIAB_CURRENCY` : Devise pour les limites Liability (obligatoire)

**Colonnes additionnelles recommandées** :
- `industry` : Généralement "Transportation"
- `sic_code` : Généralement 4512 (Air Transportation)
- `REGION` : Important pour la segmentation géographique

**Valeurs typiques** :
- `line_of_business` : "Aviation"
- Exposition : Généralement entre 10M et 300M

#### Casualty

Pour les bordereaux situés dans `bordereaux/casualty/` :

**Colonnes de devises obligatoires** :
- `ORIGINAL_CURRENCY` : Devise pour les limites (obligatoire)

**Colonnes additionnelles recommandées** :
- `industry` : Secteur d'activité (Retail, Manufacturing, Services, etc.)
- `sic_code` : Code SIC spécifique au secteur
- `COUNTRY` : Pays de l'entreprise assurée

**Valeurs typiques** :
- `line_of_business` : "Casualty"
- Exposition : Variable selon le secteur (1M à 50M)

#### Property

Pour les bordereaux situés dans `bordereaux/property/` :

**Colonnes additionnelles recommandées** :
- `REGION` : Région pour l'analyse de risque géographique
- `COUNTRY` : Pays de localisation du bien

**Valeurs typiques** :
- `line_of_business` : "Property"
- Exposition : Variable selon le type de bien

## Noms de Colonnes Alternatifs (Optionnel)

Le système accepte **plusieurs noms possibles** pour la colonne d'exposure selon la ligne de business. Cela permet de travailler avec des bordereaux qui utilisent des conventions de nommage différentes sans avoir à les modifier.

### Noms Acceptés par LOB

| Line of Business | Noms de colonnes acceptés |
|------------------|---------------------------|
| **Aviation** | `exposure`, 
| **Casualty** | `exposure`, `limite`, `limit` |
| **Property** | `exposure`, `exposure` |
| **Autres** | `exposure`, `exposure` |

### Fonctionnement

- Le système **détecte automatiquement** quelle colonne est présente dans votre bordereau
- Si un nom alternatif est utilisé (ex: `limite`), il crée automatiquement la colonne `exposure` pour le moteur de calcul
- **Aucune modification de vos fichiers n'est nécessaire** - utilisez le nom qui vous convient

### Exemples

**Avec le nom standard** :
```csv
policy_id,INSURED_NAME,exposure,INCEPTION_DT,EXPIRE_DT,line_of_business
CAS-001,CARREFOUR SA,5000000,2024-01-01,2024-12-31,Casualty
```

**Avec un nom alternatif** (fonctionne aussi) :
```csv
policy_id,INSURED_NAME,limite,INCEPTION_DT,EXPIRE_DT,line_of_business
CAS-001,CARREFOUR SA,5000000,2024-01-01,2024-12-31,Casualty
```

Les deux formats sont acceptés, aucune modification requise !

### Extensibilité

Pour accepter de nouveaux noms de colonnes :

1. Modifier `EXPOSURE_COLUMN_ALIASES` dans `structures/exposure_mapping.py`
2. Ajouter le nom dans `LOB_SPECIFIC_EXPOSURE_COLUMNS` de `structures/bordereau_loader.py`

**Exemple** :
```python
# Dans exposure_mapping.py
EXPOSURE_COLUMN_ALIASES = {
    "aviation": ["hull_limit"],
    "casualty": ["limit"],
}
```

## Structure de Dossiers

Les bordereaux doivent être organisés par **ligne de business** dans des sous-dossiers :

```
bordereaux/
├── aviation/        # Bordereaux Aviation
├── property/        # Bordereaux Property
├── casualty/        # Bordereaux Casualty
└── test/           # Bordereaux de test
```

**Avantages de cette organisation** :
- Détection automatique de la ligne de business du bordereau
- Liaison automatique au programme de réassurance correspondant
- Organisation claire des données par métier
- Facilite la validation spécifique par ligne de business

## Exemples

### Exemple Aviation (avec policy_id optionnel)

```csv
policy_id,INSURED_NAME,COUNTRY,line_of_business,HULL_CURRENCY,LIAB_CURRENCY,HULL_LIMIT,LIAB_LIMIT,HULL_SHARE,LIAB_SHARE,INCEPTION_DT,EXPIRE_DT
AVI-2024-001,AIR FRANCE-KLM,France,Aviation,USD,USD,25000000,100000000,0.15,0.10,2024-01-01,2024-12-31
AVI-2024-002,LUFTHANSA GROUP,Germany,Aviation,USD,USD,30000000,500000000,0.12,0.08,2024-02-15,2025-02-14
```

### Exemple Casualty (avec policy_id optionnel)

```csv
policy_id,INSURED_NAME,COUNTRY,line_of_business,CURRENCY,exposure,INCEPTION_DT,EXPIRE_DT
CAS-2024-001,CARREFOUR SA,France,Casualty,EUR,8500000,2024-01-01,2024-12-31
CAS-2024-002,MICHELIN GROUP,France,Casualty,EUR,15000000,2024-02-01,2025-01-31
```

### Exemple Property (sans policy_id)

```csv
INSURED_NAME,REGION,line_of_business,exposure,INCEPTION_DT,EXPIRE_DT
ENTREPRISE DUPONT SAS,EMEA,Property,500000,2024-01-01,2024-12-31
GLOBAL CORP LTD,APAC,Property,1200000,2024-03-01,2025-02-28
```

## Validation

Le système valide automatiquement :

✅ **Validations de structure** :
- Présence de toutes les colonnes requises
- Absence de colonnes inconnues
- Format des dates (YYYY-MM-DD)
- Types de données numériques pour l'exposure

✅ **Validations métier** :
- `insured_name` en MAJUSCULES uniquement
- Expositions non négatives (warning si zéro)
- Date d'expiration > date de début
- Cohérence entre la ligne de business et le dossier
- **Validation des devises** :
  - Aviation : Au moins `HULL_CURRENCY` ou `LIAB_CURRENCY` doit être présent
  - Casualty : `ORIGINAL_CURRENCY` doit être présent

❌ **Erreurs bloquantes** :
- Colonnes requises manquantes
- Dates invalides ou inversées
- Expositions négatives
- `insured_name` non en majuscules
- Colonnes inconnues
- **Colonnes de devises manquantes ou incorrectes** :
  - Aviation : Absence de `HULL_CURRENCY` et `LIAB_CURRENCY`
  - Casualty : Absence de `ORIGINAL_CURRENCY`

## Relation Bordereau-Programme

### Deux Niveaux de Line of Business

1. **Line of Business du Bordereau** (niveau dossier)
   - Détermine quel programme s'applique
   - Détectée automatiquement depuis la structure de dossiers
   - Exemple : `aviation/`, `property/`, `casualty/`

2. **Line of Business de la Police** (colonne `line_of_business`)
   - Peut différer de la ligne du bordereau
   - Utilisée pour le matching de conditions spécifiques
   - Permet une granularité fine dans le programme

**Exemple** : Un bordereau Aviation peut contenir des polices avec différentes sous-catégories d'aviation, mais toutes relèvent du programme Aviation global.

## Migration depuis l'Ancien Format

Si vous avez des bordereaux avec l'ancien format :
- `inception_date` → `INCEPTION_DT`
- `expiry_date` → `EXPIRE_DT`
- Valeurs `insured_name` → Convertir en MAJUSCULES

## Chargement Programmatique

```python
from src.domain.bordereau import Bordereau

# Chargement automatique avec détection de la ligne de business
bordereau = Bordereau.from_csv("examples/bordereaux/aviation/bordereau_aviation_axa_xl.csv")

# Ou spécification manuelle
bordereau = Bordereau.from_csv("path/to/bordereau.csv", uw_dept="aviation")
```

