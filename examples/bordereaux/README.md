# Bordereaux - Conventions et Structure

## Structure de Dossiers

Les bordereaux doivent être organisés par **ligne de business** (Line of Business) dans des sous-dossiers :

```
bordereaux/
├── aviation/        # Bordereaux Aviation
├── property/        # Bordereaux Property
├── casualty/        # Bordereaux Casualty
└── test/           # Bordereaux de test
```

Cette organisation permet :
- De détecter automatiquement la ligne de business du bordereau
- De relier automatiquement le bordereau au bon programme
- D'organiser clairement les données par métier

## Conventions de Nommage des Colonnes

### Colonnes Requises

Toutes les colonnes suivantes sont **obligatoires** :

| Colonne | Nom Exact | Format | Description |
|---------|-----------|--------|-------------|
| Insured Name | `INSURED_NAME` | **MAJUSCULES** | Nom de l'assuré (DOIT être en capitales) |
| Exposition | `exposition` | Nombre (millions) | Montant d'exposition en millions |
| Inception Date | `INCEPTION_DT` | **YYYY-MM-DD** | Date de début de couverture |
| Expiry Date | `EXPIRE_DT` | **YYYY-MM-DD** | Date de fin de couverture |
| Line of Business | `line_of_business` | Texte | Ligne de business (doit correspondre au dossier) |

⚠️ **IMPORTANT** :
- Les noms de colonnes pour les dates sont en **MAJUSCULES** : `INCEPTION_DT`, `EXPIRE_DT`
- Le champ `INSURED_NAME` doit contenir uniquement des valeurs en **MAJUSCULES**
- Les expositions sont en **millions** (ex: `25` pour 25 millions)

### Colonnes Optionnelles

| Colonne | Nom Exact | Format | Description |
|---------|-----------|--------|-------------|
| Policy ID | `policy_id` | Texte | Identifiant unique de la police (pour tracking/reporting) |

### Colonnes Dimensionnelles (Optionnelles)

Ces colonnes sont utilisées pour le matching des sections dans les programmes :

- `BUSCL_COUNTRY_CD` : Code pays
- `BUSCL_REGION` : Région géographique
- `BUSCL_CLASS_OF_BUSINESS_1` : Classe de business niveau 1
- `BUSCL_CLASS_OF_BUSINESS_2` : Classe de business niveau 2
- `BUSCL_CLASS_OF_BUSINESS_3` : Classe de business niveau 3
- `BUSCL_LIMIT_CURRENCY_CD` : Code devise
- `industry` : Industrie
- `sic_code` : Code SIC
- `include` : Indicateur d'inclusion/exclusion

## Exemples

### Exemple Aviation (avec policy_id optionnel)

```csv
policy_id,INSURED_NAME,BUSCL_COUNTRY_CD,line_of_business,exposition,INCEPTION_DT,EXPIRE_DT
AVI-2024-001,AIR FRANCE-KLM,France,Aviation,25,2024-01-01,2024-12-31
AVI-2024-002,LUFTHANSA GROUP,Germany,Aviation,30,2024-02-15,2025-02-14
```

### Exemple Property (sans policy_id)

```csv
INSURED_NAME,BUSCL_REGION,line_of_business,exposition,INCEPTION_DT,EXPIRE_DT
ENTREPRISE DUPONT SAS,EMEA,Property,0.5,2024-01-01,2024-12-31
GLOBAL CORP LTD,APAC,Property,1.2,2024-03-01,2025-02-28
```

## Validation

Le système valide automatiquement :

✅ **Validations de structure** :
- Présence de toutes les colonnes requises
- Absence de colonnes inconnues
- Format des dates (YYYY-MM-DD)
- Types de données numériques pour l'exposition

✅ **Validations métier** :
- `insured_name` en MAJUSCULES uniquement
- Expositions non négatives (warning si zéro)
- Date d'expiration > date de début
- Cohérence entre la ligne de business et le dossier

❌ **Erreurs bloquantes** :
- Colonnes requises manquantes
- Dates invalides ou inversées
- Expositions négatives
- `insured_name` non en majuscules
- Colonnes inconnues

## Relation Bordereau-Programme

### Deux Niveaux de Line of Business

1. **Line of Business du Bordereau** (niveau dossier)
   - Détermine quel programme s'applique
   - Détectée automatiquement depuis la structure de dossiers
   - Exemple : `aviation/`, `property/`, `casualty/`

2. **Line of Business de la Police** (colonne `line_of_business`)
   - Peut différer de la ligne du bordereau
   - Utilisée pour le matching de sections spécifiques
   - Permet une granularité fine dans le programme

**Exemple** : Un bordereau Aviation peut contenir des polices avec différentes sous-catégories d'aviation, mais toutes relèvent du programme Aviation global.

## Migration depuis l'Ancien Format

Si vous avez des bordereaux avec l'ancien format :
- `inception_date` → `INCEPTION_DT`
- `expiry_date` → `EXPIRE_DT`
- Valeurs `insured_name` → Convertir en MAJUSCULES

## Chargement Programmatique

```python
from structures import load_bordereau

# Chargement automatique avec détection de la ligne de business
df = load_bordereau("examples/bordereaux/aviation/bordereau_aviation_axa_xl.csv")

# Ou spécification manuelle
df = load_bordereau("path/to/bordereau.csv", line_of_business="Aviation")
```

