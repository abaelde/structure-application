# Program Creation - Data Model Constraints

Ce document définit les contraintes du modèle de données pour la création de programmes de réassurance.

## Structure des Fichiers Excel

Chaque programme doit être un fichier Excel avec **3 feuilles obligatoires** :

### 1. Feuille "program" (1 ligne)
**Contraintes :**
- **REPROG_ID_PRE** : INTEGER, clé primaire auto-incrémentée (commence à 1)
- **REPROG_TITLE** : VARCHAR(255), nom du programme (obligatoire)
- **CED_ID_PRE** : INTEGER, ID du cédant (peut être NULL)
- **CED_NAME_PRE** : VARCHAR(255), nom du cédant (peut être NULL)
- **REPROG_ACTIVE_IND** : BOOLEAN, indicateur d'activation (défaut: TRUE)
- **REPROG_COMMENT** : VARCHAR, commentaires (peut être NULL)
- **REPROG_UW_DEPARTMENT_CD** : VARCHAR(255), code département UW (peut être NULL)
- **REPROG_UW_DEPARTMENT_NAME** : VARCHAR(255), nom département UW (peut être NULL)
- **REPROG_UW_DEPARTMENT_LOB_CD** : VARCHAR(255), code LOB département (peut être NULL)
- **REPROG_UW_DEPARTMENT_LOB_NAME** : VARCHAR(255), nom LOB département (peut être NULL)
- **BUSPAR_CED_REG_CLASS_CD** : VARCHAR(255), code classe réglementaire (peut être NULL)
- **BUSPAR_CED_REG_CLASS_NAME** : VARCHAR(255), nom classe réglementaire (peut être NULL)
- **REPROG_MAIN_CURRENCY_CD** : VARCHAR(255), code devise principale (peut être NULL)
- **REPROG_MANAGEMENT_REPORTING_LOB_CD** : VARCHAR(255), code LOB reporting (peut être NULL)

### 2. Feuille "structures" (n lignes)
**Contraintes :**
- **INSPER_ID_PRE** : INTEGER PRIMARY KEY, clé primaire auto-incrémentée (commence à 1)
- **BUSINESS_ID_PRE** : VARCHAR(255), Tnumber (peut être NULL)
- **TYPE_OF_PARTICIPATION_CD** : VARCHAR(255), type de participation (quota_share, excess_of_loss) (obligatoire)
- **TYPE_OF_INSURED_PERIOD_CD** : VARCHAR(255), type de période assurée (peut être NULL)
- **ACTIVE_FLAG_CD** : BOOLEAN, indicateur d'activation (défaut: TRUE)
- **INSPER_EFFECTIVE_DATE** : DATE, date effective (peut être NULL)
- **INSPER_EXPIRY_DATE** : DATE, date d'expiration (peut être NULL)
- **REPROG_ID_PRE** : INTEGER, référence au programme (obligatoire)
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

### 3. Feuille "conditions" (n lignes)
**Contraintes :**

#### Clés et Références
- **BUSCL_ID_PRE** : INTEGER PRIMARY KEY, clé primaire auto-incrémentée (commence à 1)
- **REPROG_ID_PRE** : INTEGER, référence au programme (obligatoire)
- **CED_ID_PRE** : INTEGER, référence au cédant (peut être NULL)
- **BUSINESS_ID_PRE** : INTEGER, référence au business (peut être NULL)
- **INSPER_ID_PRE** : INTEGER, référence vers structures.INSPER_ID_PRE (obligatoire)

#### Exclusions et Noms
- **BUSCL_EXCLUDE_CD** : VARCHAR(255), ENUM: 'INCLUDE' ou 'EXCLUDE' (peut être NULL)
- **BUSCL_ENTITY_NAME_CED** : VARCHAR(255), nom d'entité cédante (peut être NULL)
- **POL_RISK_NAME_CED** : VARCHAR(255), nom du risque de police (peut être NULL)

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
1. **BUSINESS_TITLE** : Doit être unique dans la feuille structures
2. **INSPER_ID_PRE** dans conditions : Doit référencer un INSPER_ID_PRE existant dans structures
3. **REPROG_ID_PRE** dans structures : Doit référencer le REPROG_ID_PRE du programme parent
4. **REPROG_ID_PRE** dans conditions : Doit référencer le REPROG_ID_PRE du programme parent
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
- ✅ **Plus maintenable** : Un seul endroit pour gérer la conversion Excel
- ✅ **Moins d'erreurs** : IDs et champs gérés automatiquement
- ✅ **Réutilisable** : Les Builders sont aussi utilisés dans les tests

**Scripts disponibles :**
- `create_single_quota_share.py` - Exemple simple (61 lignes au lieu de 177)
- `create_casualty_AIG.py` - QS avec 2 conditions (94 lignes au lieu de 236)
- `create_aviation_old_republic.py` - 3 XOL parallèles (106 lignes au lieu de 248)
- `create_aviation_AXA_XL.py` - Complexe multi-devises (156 lignes au lieu de 473)

**Utilitaires :**
- `excel_utils.py` - Fonction `program_to_excel()` pour convertir Program → Excel
- `regenerate_all_programs.py` - Régénération en lot
- `combine_all_programs.py` - Combinaison de tous les programmes en une base de données simulée

### 📝 Comment créer un nouveau programme avec les Builders

#### Exemple 1 : Quota Share simple

```python
from tests.builders import build_quota_share, build_program
from excel_utils import program_to_excel

# Créer une structure Quota Share 30%
qs = build_quota_share(name="QS_30", cession_pct=0.30, claim_basis="risk_attaching", inception_date="2024-01-01", expiry_date="2025-01-01")

# Créer le programme
program = build_program(
    name="MY_PROGRAM_2024",
    structures=[qs],
    underwriting_department="aviation"
)

# Sauvegarder en Excel
program_to_excel(program, "../programs/my_program.xlsx")
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
program_to_excel(program, "../programs/qs_multi_currency.xlsx")
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
program_to_excel(program, "../programs/qs_then_xol.xlsx")
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
program_to_excel(program, "../programs/multi_xol.xlsx")
```

#### Exemple 5 : condition avec exclusions

```python
from tests.builders import build_condition, build_quota_share

qs = build_quota_share(
    name="QS_WITH_EXCLUSIONS",
    conditions_config=[
        {
            "cession_pct": 0.30,
            "signed_share": 0.10,
            "country_cd": "Iran",
            "exclude_cd": "exclude",  # condition d'exclusion
        },
        {
            "cession_pct": 0.30,
            "signed_share": 0.10,
            # Pas de country_cd = condition catch-all pour tous les autres pays
        },
    ]
)

program = build_program(name="QS_EXCL_2024", structures=[qs], underwriting_department="casualty")
program_to_excel(program, "../programs/qs_exclusions.xlsx")
```

### Auto-ajustement des colonnes Excel

La fonction `program_to_excel()` appelle automatiquement `auto_adjust_column_widths()` pour ajuster la largeur des colonnes en fonction de leur contenu, améliorant ainsi la lisibilité des fichiers générés.

**Paramètres optionnels de `program_to_excel()` :**
- `min_width` : Largeur minimale des colonnes (défaut : 10)
- `max_width` : Largeur maximale des colonnes (défaut : 50)

```python
program_to_excel(program, "output.xlsx", min_width=12, max_width=60)
```

### Base de Données Simulée : all_programs.xlsx

Le script `combine_all_programs.py` crée un fichier `all_programs.xlsx` qui simule une base de données avec plusieurs programmes :

```bash
uv run python examples/program_creation/combine_all_programs.py
```

**Fonctionnement :**
1. Lit tous les fichiers `.xlsx` du dossier `examples/programs/`
2. Renumérote les IDs de manière séquentielle (simule l'auto-increment d'une base de données) :
   - `REPROG_ID_PRE` : 1, 2, 3, ... (un par programme)
   - `INSPER_ID_PRE` : continue séquentiellement à travers tous les programmes
   - `BUSCL_ID_PRE` : continue séquentiellement à travers toutes les conditions
3. Maintient les relations entre tables (foreign keys)
4. Concatène toutes les données en un seul fichier

**Exemple de renumération :**
```
Programme 1 (aviation_axa_xl_2024.xlsx) :
  - REPROG_ID_PRE : 1
  - INSPER_ID_PRE : 1-7
  - BUSCL_ID_PRE : 1-35

Programme 2 (aviation_old_republic_2024.xlsx) :
  - REPROG_ID_PRE : 2
  - INSPER_ID_PRE : 8-10 (continue après 7)
  - BUSCL_ID_PRE : 36-41 (continue après 35)
```

**Usage :**
Le fichier `all_programs.xlsx` est une **base de données simulée** qui représente ce que vous auriez dans une vraie base de données avec plusieurs programmes. 

⚠️ **Note** : Ce fichier n'est pas destiné à être utilisé directement avec le `ProgramLoader` actuel, qui est conçu pour charger un seul programme à la fois. Il sert de référence pour visualiser comment plusieurs programmes coexisteraient dans une base de données réelle.

## Validation

Avant de créer un nouveau programme, vérifiez :
1. Toutes les contraintes structurelles sont respectées
2. Les types de participation correspondent aux paramètres
3. Les références entre feuilles sont cohérentes
4. Les valeurs numériques sont dans les bonnes unités (valeur absolue)