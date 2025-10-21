# Program Creation - Data Model Constraints

Ce document définit les contraintes du modèle de données pour la création de programmes de réassurance.

## Structure des Fichiers CSV

Chaque programme doit être un dossier CSV avec **3 fichiers obligatoires** :

### 1. Fichier "program.csv" (1 ligne)
**Contraintes :**
- **REINSURANCE_PROGRAM_ID** : INTEGER, clé primaire auto-incrémentée (commence à 1)
- **TITLE** : VARCHAR(255), nom du programme (obligatoire)
- **CED_ID_PRE** : INTEGER, ID du cédant (peut être NULL)
- **CED_NAME_PRE** : VARCHAR(255), nom du cédant (peut être NULL)
- **ACTIVE_IND** : BOOLEAN, indicateur d'activation (défaut: TRUE)
- **ADDITIONAL_INFO** : VARCHAR, commentaires (peut être NULL)
- **UW_DEPARTMENT_CODE** : VARCHAR(255), code département UW (peut être NULL)
- **REPROG_UW_DEPARTMENT_NAME** : VARCHAR(255), nom département UW (peut être NULL)
- **UW_LOB** : VARCHAR(255), code LOB département (peut être NULL)
- **REPROG_UW_DEPARTMENT_LOB_NAME** : VARCHAR(255), nom LOB département (peut être NULL)
- **BUSPAR_CED_REG_CLASS_CD** : VARCHAR(255), code classe réglementaire (peut être NULL)
- **BUSPAR_CED_REG_CLASS_NAME** : VARCHAR(255), nom classe réglementaire (peut être NULL)
- **MAIN_CURRENCY_CD** : VARCHAR(255), code devise principale (peut être NULL)
- **REPROG_MANAGEMENT_REPORTING_LOB_CD** : VARCHAR(255), code LOB reporting (peut être NULL)

### 2. Fichier "structures.csv" (n lignes)
**Contraintes :**
- **INSPER_ID_PRE** : INTEGER PRIMARY KEY, clé primaire auto-incrémentée (commence à 1)
- **BUSINESS_ID_PRE** : VARCHAR(255), Tnumber (peut être NULL)
- **TYPE_OF_PARTICIPATION_CD** : VARCHAR(255), type de participation (quota_share, excess_of_loss) (obligatoire)
- **TYPE_OF_INSURED_PERIOD_CD** : VARCHAR(255), type de période assurée (peut être NULL)
- **ACTIVE_FLAG_CD** : BOOLEAN, indicateur d'activation (défaut: TRUE)
- **INSPER_EFFECTIVE_DATE** : DATE, date effective (peut être NULL)
- **INSPER_EXPIRY_DATE** : DATE, date d'expiration (peut être NULL)
- **REINSURANCE_PROGRAM_ID** : INTEGER, référence au programme (obligatoire)
- **BUSINESS_TITLE** : VARCHAR(255), titre de la structure (obligatoire)
- **INSPER_LAYER_NO** : INTEGER, numéro de couche (peut être NULL)
- **INSPER_MAIN_CURRENCY_CD** : VARCHAR(255), devise principale (peut être NULL)
- **INSPER_UW_YEAR** : INTEGER, année UW (peut être NULL)
- **INSPER_CONTRACT_ORDER** : INTEGER,(rempli avec NULL)
- **INSPER_PREDECESSOR_TITLE** : VARCHAR(255), nom de la structure antécédente pour l'inuring (NULL = entry point)
- **INSPER_CONTRACT_FORM_CD_SLAV** : VARCHAR(255), code forme de contrat (peut être NULL)
- **INSPER_CONTRACT_LODRA_CD_SLAV** : VARCHAR(255), code LODRA contrat (peut être NULL)
- **INSPER_CONTRACT_COVERAGE_CD_SLAV** : VARCHAR(255), code couverture contrat (peut être NULL)
- **INSPER_CLAIM_BASIS_CD** : VARCHAR(255), base de sinistre (risk_attaching, loss_occurring) (peut être NULL)
- **INSPER_LODRA_CD_SLAV** : VARCHAR(255), code LODRA (peut être NULL)
- **INSPER_LOD_TO_RA_DATE_SLAV** : DATE, date LOD to RA (peut être NULL)
- **INSPER_COMMENT** : VARCHAR, commentaires (peut être NULL)

### 3. Fichier "conditions.csv" (n lignes)
**Contraintes :**

#### Clés et Références
- **BUSCL_ID_PRE** : INTEGER PRIMARY KEY, clé primaire auto-incrémentée (commence à 1)
- **REINSURANCE_PROGRAM_ID** : INTEGER, référence au programme (obligatoire)
- **CED_ID_PRE** : INTEGER, référence au cédant (peut être NULL)
- **BUSINESS_ID_PRE** : INTEGER, référence au business (peut être NULL)
- **INSPER_ID_PRE** : INTEGER, référence vers structures.INSPER_ID_PRE (obligatoire)

#### Noms d'entités
- **BUSCL_ENTITY_NAME_CED** : VARCHAR(255), nom d'entité cédante (peut être NULL)
- **POL_RISK_NAME_CED** : VARCHAR(255), nom du risque de police (peut être NULL)

> **Note** : Les exclusions sont maintenant gérées au niveau programme via la table `exclusions.csv` (voir section "Exclusions globales de programme").

#### Dimensions Géographiques et Produits
- **BUSCL_COUNTRY_CD** : VARCHAR(255), code pays (peut être NULL = pas de condition)
- **BUSCL_COUNTRY** : VARCHAR(255), nom du pays (peut être NULL)
- **BUSCL_REGION** : VARCHAR(255), région (peut être NULL = pas de condition)
- **BUSCL_CLASS_OF_BUSINESS_1** : VARCHAR(255), classe de business niveau 1 (peut être NULL = pas de condition)
- **BUSCL_CLASS_OF_BUSINESS_2** : VARCHAR(255), classe de business niveau 2 (peut être NULL = pas de condition)
- **BUSCL_CLASS_OF_BUSINESS_3** : VARCHAR(255), classe de business niveau 3 (peut être NULL = pas de condition)

#### Devise et Limites
- **BUSCL_LIMIT_CURRENCY_CD** : VARCHAR(255), devise des limites (peut être NULL = pas de condition)
- **AAD_100** : DECIMAL, AAD (Annual Aggregate Deductible) en valeur absolue (peut être NULL)
- **LIMIT_100** : DECIMAL, limite générale en valeur absolue (peut être NULL)
- **LIMIT_FLOATER_100** : DECIMAL, limite flottante en valeur absolue (peut être NULL)
- **ATTACHMENT_POINT_100** : DECIMAL, point d'attachement en valeur absolue (peut être NULL pour QS)
- **OLW_100** : DECIMAL, OLW (Original Line Written) en valeur absolue (peut être NULL)
- **LIMIT_OCCURRENCE_100** : DECIMAL, limite par occurrence en valeur absolue (peut être NULL pour QS)
- **LIMIT_AGG_100** : DECIMAL, limite agrégée en valeur absolue (peut être NULL)

#### Cession et Rétention
- **CESSION_PCT** : DECIMAL(0-1), pourcentage de cession (obligatoire pour QS, NULL pour XOL)
- **RETENTION_PCT** : DECIMAL(0-1), pourcentage de rétention (peut être NULL)
- **SUPI_100** : DECIMAL, SUPI en valeur absolue (peut être NULL)

#### Primes
- **BUSCL_PREMIUM_CURRENCY_CD** : VARCHAR(255), devise des primes (peut être NULL)
- **BUSCL_PREMIUM_GROSS_NET_CD** : VARCHAR(255), prime brute/nette (peut être NULL)
- **PREMIUM_RATE_PCT** : DECIMAL(0-1), taux de prime en % (peut être NULL)
- **PREMIUM_DEPOSIT_100** : DECIMAL, dépôt de prime en valeur absolue (peut être NULL)
- **PREMIUM_MIN_100** : DECIMAL, prime minimum en valeur absolue (peut être NULL)

#### Couverture et Participations
- **BUSCL_LIABILITY_1_LINE_100** : DECIMAL, ligne de responsabilité 1 en valeur absolue (peut être NULL)
- **MAX_COVER_PCT** : DECIMAL(0-1), couverture maximum en % (peut être NULL)
- **MIN_EXCESS_PCT** : DECIMAL(0-1), excédent minimum en % (peut être NULL)
- **SIGNED_SHARE_PCT** : DECIMAL(0-1), part signée en % (peut être NULL)
- **AVERAGE_LINE_SLAV_CED** : DECIMAL, ligne moyenne (peut être NULL)
- **PML_DEFAULT_PCT** : DECIMAL(0-1), PML par défaut en % (peut être NULL)
- **LIMIT_EVENT** : DECIMAL, limite par événement (peut être NULL)
- **NO_OF_REINSTATEMENTS** : INTEGER, nombre de reconstitutions (peut être NULL)

## Contraintes de Cohérence

### Contraintes Structurelles
1. **BUSINESS_TITLE** : Doit être unique dans le fichier structures.csv
2. **INSPER_ID_PRE** dans conditions : Doit référencer un INSPER_ID_PRE existant dans structures.csv
3. **REINSURANCE_PROGRAM_ID** dans structures.csv : Doit référencer le REINSURANCE_PROGRAM_ID du programme parent
4. **REINSURANCE_PROGRAM_ID** dans conditions.csv : Doit référencer le REINSURANCE_PROGRAM_ID du programme parent
5. **BUSCL_ID_PRE** : Doit être unique et auto-incrémenté
6. **INSPER_PREDECESSOR_TITLE** : Si non NULL, doit référencer un BUSINESS_TITLE existant dans le même programme

### Mécanisme d'Inuring
Le **mécanisme d'inuring** permet de chaîner les structures de réassurance :

1. **Entry points** : Structures sans prédécesseur (INSPER_PREDECESSOR_TITLE = NULL)
   - S'appliquent directement sur l'exposure initiale de la police
   - Peuvent être multiples (structures parallèles)

2. **Structures chaînées** : Structures avec prédécesseur
   - S'appliquent sur la **rétention** du prédécesseur (exposure - cession)
   - Permet de simuler des structures empilées ou sur la rétention

3. **Structures parallèles** : Plusieurs structures avec le même prédécesseur
   - Toutes s'appliquent sur la même base (rétention du prédécesseur)
   - Exemple : Plusieurs XOL sur la rétention d'un Quota Share

**Exemple :**
```
QS_1 (predecessor: None)     → Entry point, appliqué sur exposure initiale
├─ XOL_1 (predecessor: QS_1) → Appliqué sur rétention du QS_1
├─ XOL_2 (predecessor: QS_1) → Appliqué sur rétention du QS_1 (parallèle à XOL_1)
└─ XOL_3 (predecessor: QS_1) → Appliqué sur rétention du QS_1 (parallèle à XOL_1 et XOL_2)
```

### Rescaling Automatique
Quand un **Excess of Loss** s'applique après un **Quota Share** :
- Les limites (LIMIT_100) et points d'attachement (ATTACHMENT_POINT_100) du XOL sont automatiquement **rescalés**
- Facteur de rescaling = taux de rétention du QS
- Exemple : QS avec cession 25% (rétention 75%) → XOL défini à 100M xs 50M devient 75M xs 37.5M

### Contraintes Logiques
1. **quota_share** : 
   - `CESSION_PCT` obligatoire (0-1)
   - `ATTACHMENT_POINT_100` et `LIMIT_OCCURRENCE_100` doivent être NULL
2. **excess_of_loss** :
   - `ATTACHMENT_POINT_100` et `LIMIT_OCCURRENCE_100` obligatoires (≥ 0)
   - `CESSION_PCT` doit être NULL

### Contraintes de Valeurs
1. **Montants** : Tous les montants sont exprimés en valeur absolue (unités réelles)
2. **Pourcentages** : Tous les pourcentages sont exprimés en décimal (0.25 = 25%)
3. **Dates** : Format ISO (YYYY-MM-DD) ou NULL

## Exclusions Globales de Programme

### Nouveau système d'exclusions

Depuis la migration, les exclusions sont gérées au niveau programme via une table dédiée `exclusions.csv`.

### Structure de la table exclusions

| Colonne | Type | Description |
|---------|------|-------------|
| **EXCL_REASON** | VARCHAR(255) | Raison de l'exclusion (optionnel) |
| **EXCL_EFFECTIVE_DATE** | DATE | Date d'effet de l'exclusion (optionnel) |
| **EXCL_EXPIRY_DATE** | DATE | Date d'expiration de l'exclusion (optionnel) |
| **BUSCL_COUNTRY_CD** | VARCHAR(255) | Pays à exclure (valeurs multiples séparées par `;`) |
| **BUSCL_REGION** | VARCHAR(255) | Région à exclure (valeurs multiples séparées par `;`) |
| **BUSCL_CLASS_OF_BUSINESS_1** | VARCHAR(255) | Classe de business à exclure (valeurs multiples séparées par `;`) |
| **BUSCL_CLASS_OF_BUSINESS_2** | VARCHAR(255) | Classe de business niveau 2 à exclure (valeurs multiples séparées par `;`) |
| **BUSCL_CLASS_OF_BUSINESS_3** | VARCHAR(255) | Classe de business niveau 3 à exclure (valeurs multiples séparées par `;`) |
| **BUSCL_ENTITY_NAME_CED** | VARCHAR(255) | Entité cédante à exclure (valeurs multiples séparées par `;`) |
| **POL_RISK_NAME_CED** | VARCHAR(255) | Risque de police à exclure (valeurs multiples séparées par `;`) |
| **BUSCL_LIMIT_CURRENCY_CD** | VARCHAR(255) | Devise à exclure (valeurs multiples séparées par `;`) |

### Exemples d'exclusions

#### Exclusions simples par pays
```csv
EXCL_REASON,EXCL_EFFECTIVE_DATE,EXCL_EXPIRY_DATE,BUSCL_COUNTRY_CD,BUSCL_REGION,BUSCL_CLASS_OF_BUSINESS_1
"Sanctions Iran",,,Iran,,,
"Sanctions Russia",,,Russia,,,
```

#### Exclusions avec dates
```csv
EXCL_REASON,EXCL_EFFECTIVE_DATE,EXCL_EXPIRY_DATE,BUSCL_COUNTRY_CD,BUSCL_CLASS_OF_BUSINESS_1
"Temporary sanctions",2024-06-01,2024-12-31,Iran,,
"Scope Aviation 2025",2025-01-01,2026-01-01,,AVIATION
```

#### Exclusions multiples
```csv
EXCL_REASON,EXCL_EFFECTIVE_DATE,EXCL_EXPIRY_DATE,BUSCL_COUNTRY_CD,BUSCL_CLASS_OF_BUSINESS_1
"Multiple sanctions",,,Iran;Russia;Syria,,
```

### Logique d'exclusion

1. **Évaluation temporelle** : Si des dates sont fournies, l'exclusion n'est active que pendant la période `[EXCL_EFFECTIVE_DATE, EXCL_EXPIRY_DATE[`
2. **Matching des dimensions** : Une police est exclue si elle correspond à **toutes** les dimensions spécifiées dans une règle d'exclusion
3. **Valeurs multiples** : Les valeurs multiples sont séparées par `;` (ex: `Iran;Russia`)
4. **Priorité** : Les exclusions sont évaluées **avant** l'application des structures

## Format de Données

### Format Actuel
- **Programme** : Tous les champs REPROG_*
- **Structures** : Tous les champs INSPER_* incluant **INSPER_PREDECESSOR_TITLE** pour l'inuring
- **conditions** : `INSPER_ID_PRE` (référence par ID), tous les champs BUSCL_*

### Conventions
- **Montants** : Tous les montants sont en **valeur absolue** (pas en millions)
- **Inuring** : Utilisation de `INSPER_PREDECESSOR_TITLE` pour chaîner les structures
- **Ordre** : `INSPER_CONTRACT_ORDER` est **deprecated** et doit être NULL

## Scripts de Création

### 🚀 Nouvelle approche avec les Builders (Recommandée)

Tous les scripts de création utilisent maintenant les **Builders** pour créer les programmes de manière concise et expressive.

**Avantages :**
- ✅ **90% moins de code** : Focus sur la logique métier
- ✅ **Plus lisible** : API fluide et intuitive
- ✅ **Plus maintenable** : Un seul endroit pour gérer la conversion CSV
- ✅ **Moins d'erreurs** : IDs et champs gérés automatiquement
- ✅ **Réutilisable** : Les Builders sont aussi utilisés dans les tests

**Scripts disponibles :**
- `create_single_quota_share.py` - Exemple simple (61 lignes au lieu de 177)
- `create_casualty_AIG.py` - QS avec 2 conditions (94 lignes au lieu de 236)
- `create_aviation_old_republic.py` - 3 XOL parallèles (106 lignes au lieu de 248)
- `create_aviation_AXA_XL.py` - Complexe multi-devises (156 lignes au lieu de 473)

**Utilitaires :**
- `ProgramManager` - Gestionnaire unifié pour charger/sauvegarder des programmes
- `regenerate_all_programs.py` - Régénération en lot de tous les programmes
- `combine_all_programs.py` - Combinaison de tous les programmes en une base de données simulée

### 📝 Comment créer un nouveau programme avec les Builders

#### Exemple 1 : Quota Share simple

```python
from tests.builders import build_quota_share, build_program
from src.managers import ProgramManager

# Créer une structure Quota Share 30%
qs = build_quota_share(name="QS_30", cession_pct=0.30, claim_basis="risk_attaching", inception_date="2024-01-01", expiry_date="2025-01-01")

# Créer le programme
program = build_program(
    name="MY_PROGRAM_2024",
    structures=[qs],
    underwriting_department="aviation"
)

# Sauvegarder en CSV folder
manager = ProgramManager()
manager.save(program, "../programs/my_program")
```

#### Exemple 2 : Quota Share avec plusieurs conditions (multi-devises)

```python
qs = build_quota_share(
    name="QS_MULTI_CURRENCY",
    conditions_config=[
        {
            "cession_pct": 0.25,
            "limit": 100_000_000,
            "signed_share": 0.10,
            "currency_cd": "USD",
        },
        {
            "cession_pct": 0.30,
            "limit": 75_000_000,
            "signed_share": 0.10,
            "currency_cd": "EUR",
        },
    ],
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2025-01-01"
)

program = build_program(name="QS_MULTI_2024", structures=[qs], underwriting_department="aviation")
# Sauvegarder en CSV folder
from src.managers import ProgramManager
manager = ProgramManager()
manager.save(program, "../programs/qs_multi_currency")
```

#### Exemple 3 : Excess of Loss avec inuring

```python
from tests.builders import build_quota_share, build_excess_of_loss, build_program

# QS en premier (entry point)
qs = build_quota_share(name="QS_25", cession_pct=0.25, claim_basis="risk_attaching", inception_date="2024-01-01", expiry_date="2025-01-01")

# XOL qui s'applique sur la rétention du QS (inuring)
xol = build_excess_of_loss(
    name="XOL_50xs20",
    attachment=20_000_000,
    limit=50_000_000,
    predecessor_title="QS_25",  # Inuring: s'applique après QS_25
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2025-01-01"
)

program = build_program(
    name="QS_THEN_XOL_2024",
    structures=[qs, xol],
    underwriting_department="aviation"
)
# Sauvegarder en CSV folder
from src.managers import ProgramManager
manager = ProgramManager()
manager.save(program, "../programs/qs_then_xol")
```

#### Exemple 4 : Plusieurs XOL parallèles avec conditions par pays

```python
# Créer des XOL pour plusieurs pays
countries = ["United States", "Canada", "Mexico"]

xol_1 = build_excess_of_loss(
    name="XOL_1",
    conditions_config=[
        {
            "attachment": 5_000_000,
            "limit": 10_000_000,
            "signed_share": 0.10,
            "country_cd": country,
        }
        for country in countries
    ],
    claim_basis="risk_attaching"
)

xol_2 = build_excess_of_loss(
    name="XOL_2",
    conditions_config=[
        {
            "attachment": 15_000_000,
            "limit": 20_000_000,
            "signed_share": 0.10,
            "country_cd": country,
        }
        for country in countries
    ],
    claim_basis="risk_attaching"
)

program = build_program(
    name="MULTI_XOL_2024",
    structures=[xol_1, xol_2],
    underwriting_department="aviation"
)
# Sauvegarder en CSV folder
from src.managers import ProgramManager
manager = ProgramManager()
manager.save(program, "../programs/multi_xol")
```

#### Exemple 5 : programme avec exclusions globales

```python
from tests.builders import build_condition, build_quota_share, build_program
from src.domain.exclusion import ExclusionRule

qs = build_quota_share(
    name="QS_WITH_EXCLUSIONS",
    conditions_config=[
        {
            "cession_pct": 0.30,
            "signed_share": 0.10,
            # Pas de country_cd = condition catch-all pour tous les autres pays
        },
    ]
)

program = build_program(name="QS_EXCL_2024", structures=[qs], underwriting_department="casualty")

# Ajouter les exclusions au niveau programme
exclusions = [
    ExclusionRule(
        values_by_dimension={'BUSCL_COUNTRY_CD': ['Iran']},
        reason='Sanctions Iran'
    ),
]
program.exclusions = exclusions

# Sauvegarder en CSV folder
from src.managers import ProgramManager
manager = ProgramManager()
manager.save(program, "../programs/qs_exclusions")
```

### Sauvegarde en CSV Folder

Les programmes sont maintenant sauvegardés au format CSV folder, qui est plus simple et plus portable. Chaque programme est sauvegardé dans un dossier contenant 4 fichiers CSV :

- `program.csv` - Informations générales du programme
- `structures.csv` - Toutes les structures du programme  
- `conditions.csv` - Toutes les conditions du programme
- `exclusions.csv` - Toutes les exclusions du programme (si présentes)

**Avantages du format CSV :**
- Plus simple à lire et modifier
- Compatible avec tous les outils de données
- Versioning Git-friendly
- Pas de dépendances externes

### Scripts utilitaires

#### Régénération en lot
```bash
# Régénérer tous les programmes à partir des scripts Python
uv run python examples/program_creation/regenerate_all_programs.py
```

#### Combinaison de programmes
```bash
# Combiner tous les programmes en une base de données simulée
uv run python examples/program_creation/combine_all_programs.py
```

Le script `combine_all_programs.py` crée un dossier `all_programs/` qui simule une base de données avec plusieurs programmes :
- Lit tous les dossiers CSV du dossier `examples/programs/`
- Renumérote les IDs de manière séquentielle (simule l'auto-increment d'une base de données)
- Concatène toutes les données en un seul dossier CSV
- Crée les fichiers : `program.csv`, `structures.csv`, `conditions.csv`, `exclusions.csv` (si présentes)

## Validation

Avant de créer un nouveau programme, vérifiez :
1. Toutes les contraintes structurelles sont respectées
2. Les types de participation correspondent aux paramètres
3. Les références entre feuilles sont cohérentes
4. Les valeurs numériques sont dans les bonnes unités (valeur absolue)