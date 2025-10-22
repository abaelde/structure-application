# Reinsurance Program Application System

Système d'application de programmes de réassurance sur des bordereaux.

## Architecture

### Structure du projet

```
structure-application/
├── src/                                # Code source
│   ├── domain/                         # Logique métier et modèles
│   │   ├── products/                   # Produits de réassurance (building blocks)
│   │   │   ├── quota_share.py
│   │   │   ├── excess_of_loss.py
│   │   │   └── __init__.py
│   │   ├── constants.py                # Constantes métier (PRODUCT, CLAIM_BASIS, etc.)
│   │   └── __init__.py
│   ├── loaders/                        # Chargement et validation de données
│   │   ├── program_loader.py          # Chargement de programmes depuis CSV
│   │   ├── bordereau_loader.py        # Chargement et validation de bordereaux CSV
│   │   ├── exposure_mapping.py        # Mapping de colonnes d'exposure par LoB
│   │   └── __init__.py
│   ├── engine/                         # Moteur de calcul et orchestration
│   │   ├── calculation_engine.py      # Application de programmes, matching de conditions
│   │   └── __init__.py
│   └── presentation/                   # Affichage et génération de rapports
│       ├── program_display.py         # Affichage de programmes
│       ├── report_display.py          # Génération de rapports de résultats
│       └── __init__.py
├── examples/                           # Exemples et démonstrations
│   ├── README.md                      # Documentation des exemples
│   ├── bordereaux/                    # Exemples de bordereaux (organisés par ligne de business)
│   │   ├── aviation/                  # Bordereaux Aviation
│   │   │   ├── bordereau_aviation_axa_xl.csv
│   │   │   └── bordereau_aviation_old_republic.csv
│   │   ├── test/                      # Bordereaux de test
│   │   │   ├── bordereau_exemple.csv
│   │   │   └── bordereau_multi_year_test.csv
│   │   └── README.md                  # Conventions des bordereaux
│   ├── programs/                      # Exemples de programmes
│   │   ├── program_simple_sequential/
│   │   ├── program_simple_parallel/
│   │   └── program_simple_*_updated/
│   └── scripts/                       # Scripts d'exemple
│       ├── create_simple_programs.py
│       ├── create_program_config.py
│       └── example_claim_basis_usage.py
├── program_config/                    # Configuration du programme (CSV folder)
├── PROGRAM_SPECIFICATION_GUIDE.md     # Guide de spécification des programmes
├── CLAIM_BASIS_GUIDE.md               # Guide de la logique claim_basis
├── EXCLUSION_MECHANISM.md             # Guide du mécanisme d'exclusion
├── POLICY_EXPIRY_MECHANISM.md         # Guide de vérification d'activité des polices
├── main.py                            # Point d'entrée principal
├── test_simple_programs.py            # Tests des programmes simples
├── test_new_fields.py                 # Tests des nouveaux champs
├── demo_organized_examples.py         # Démonstration de l'organisation
└── README.md                          # Documentation
```

## Concepts

### 1. Bordereau
Fichier CSV contenant les polices d'assurance avec :

**Colonnes requises :**
- `INSURED_NAME` : Nom de l'assuré (**DOIT être en MAJUSCULES**)
- `exposure` : Valeur d'exposure (**en millions**)
- `INCEPTION_DT` : Date de souscription de la police (**format YYYY-MM-DD**)
- `EXPIRE_DT` : Date d'expiration de la police (**format YYYY-MM-DD**)
- `line_of_business` : Ligne de business

**Colonnes optionnelles (pour matching de conditions) :**
- `policy_id` : Identifiant unique (optionnel, pour tracking/reporting)
- `BUSCL_COUNTRY_CD` : Code pays
- `BUSCL_REGION` : Région (APAC, EMEA, Americas, etc.)
- `BUSCL_CLASS_OF_BUSINESS_1`, `BUSCL_CLASS_OF_BUSINESS_2`, `BUSCL_CLASS_OF_BUSINESS_3` : Hiérarchie des classes de business
- `BUSCL_LIMIT_CURRENCY_CD` : Code devise
- `industry` : Industrie
- `sic_code` : Code SIC
- `include` : Champ libre pour conditions spéciales

⚠️ **IMPORTANT** : Les bordereaux doivent être organisés dans des sous-dossiers par ligne de business (aviation/, property/, casualty/, test/). Consultez [examples/bordereaux/README.md](examples/bordereaux/README.md) pour les conventions complètes.

**Vérification de l'activité des polices :**

Le système vérifie automatiquement si les polices sont encore actives à la date de calcul. Une police est considérée comme **inactive** si `EXPIRE_DT <= calculation_date`. Les polices inactives ont une exposure effective de 0 et ne génèrent aucune cession.

Pour plus de détails, consultez [POLICY_EXPIRY_MECHANISM.md](POLICY_EXPIRY_MECHANISM.md).

### 2. Produits de base
- **quota-share** : Application d'un pourcentage de cession (cession_PCT) sur l'exposure
- **Excess of Loss (XoL)** : Couverture au-dessus d'une priorité (attachment_point_100) jusqu'à une limite (limit_occurrence_100)

### 3. Program
Un fichier de configuration contient **un seul programme** qui est constitué de **plusieurs structures**.

Le programme définit :
- **Nom** : Identifiant du programme
- **Mode** : Comment les structures s'appliquent
  - `sequential` : Les structures s'appliquent successivement (la sortie de l'une devient l'entrée de la suivante)
  - `parallel` : Chaque structure s'applique indépendamment sur l'exposure initiale

### 4. Structures
Les structures sont les éléments qui composent un programme. Chaque structure :
- Est définie par son nom, son ordre d'application et le type de produit utilisé
- Possède plusieurs **conditions** qui définissent les paramètres et conditions d'application
- Peut avoir un **claim_basis** : "risk_attaching" ou "loss_occurring"
- A des dates de validité : `inception_date` et `expiry_date`

### 5. conditions
Les conditions sont les instanciations concrètes d'une structure avec :
- **Paramètres** : cession_PCT (pour quota_share), attachment_point_100 et limit_occurrence_100 (pour excess_of_loss)
- **Conditions** : Valeurs spécifiques pour les dimensions (localisation, industrie, etc.)

#### Logique de matching
Pour chaque police et chaque structure :
1. Le système cherche toutes les conditions dont les conditions matchent la police
2. Si plusieurs conditions matchent, la **plus spécifique** est choisie (celle avec le plus de conditions)
3. Si aucune condition ne matche, la structure n'est pas appliquée

**Exemple :**
- condition 1 : cession_PCT=30%, localisation=NULL → S'applique partout (générique)
- condition 2 : cession_PCT=40%, localisation=Paris → S'applique uniquement à Paris (spécifique)

Pour une police à Paris, la condition 2 sera choisie car elle est plus spécifique.

## Configuration CSV

Le dossier `program_config/` contient 3 fichiers CSV :

### Fichier "program.csv"
Définit le programme principal (une seule ligne).

| program_name | mode       |
|--------------|------------|
| PROGRAM_2024 | sequential |

### Fichier "structures.csv"
Définit les structures du programme (nom, type de produit).

| structure_name | type_of_participation    |
|----------------|-----------------|
| QS_GENERAL     | quota_share     |
| XOL_LARGE      | excess_of_loss  |

### Fichier "conditions.csv"
Définit les conditions de chaque structure avec paramètres et conditions.

| structure_name | cession_PCT | attachment_point_100 | limit_occurrence_100   | localisation | industrie |
|----------------|--------------|----------|---------|--------------|-----------|
| QS_GENERAL     | 0.30         | -        | -       | -            | -         |
| QS_GENERAL     | 0.40         | -        | -       | Paris        | -         |
| XOL_LARGE      | -            | 500000   | 1000000 | Paris        | -         |

**Notes importantes :**
- Les colonnes de dimensions (localisation, industrie) sont détectées automatiquement
- Une valeur vide (NaN) dans une colonne de dimension signifie "pas de condition sur cette dimension"
- Plusieurs conditions peuvent exister pour la même structure avec différentes combinaisons de conditions
- Le système choisit automatiquement la condition la plus spécifique (avec le plus de conditions matchées)

## Utilisation

### 🎨 Application Streamlit (Interface Graphique)

Pour une interface graphique moderne et interactive :

```bash
# Lancer l'application Streamlit
uv run streamlit run app/main.py

# Ou utiliser le script de lancement
./run_app.sh
```

L'application propose :
- 📤 Upload facile de programme (CSV folder) et bordereau (CSV)
- 📊 Visualisation interactive des résultats par police
- 🔍 Exploration détaillée de l'application des structures
- 💾 Export des résultats au format CSV
- 🎯 Interface moderne avec métriques en temps réel

Consultez [STREAMLIT_APP.md](STREAMLIT_APP.md) pour plus de détails.

### 🖥️ Interface en ligne de commande (CLI)

Pour une utilisation scriptée ou automatisée :

```bash
# Installer les dépendances
uv sync

# Appliquer un programme à un bordereau
uv run python run_program_analysis.py --program examples/programs/aviation_axa_xl_2024 --bordereau examples/bordereaux/aviation/bordereau_aviation_axa_xl.csv
```

### Cas d'usage avancé : Consolidation multi-cédantes

Le cas d'usage réel consiste à appliquer plusieurs programmes (un par cédante) à leurs bordereaux respectifs, puis à agréger les résultats par police sous-jacente.

```bash
# Vérifier le statut des mappings programme-bordereau
uv run python examples/program_bordereau_mapping.py

# Consolider tous les programmes prêts
uv run python consolidate_programs.py
```

**Ce que fait le script de consolidation :**
1. Charge tous les programmes avec leur bordereau mappé
2. Applique chaque programme à son bordereau
3. Agrège les résultats par police sous-jacente
4. Génère des statistiques consolidées par cédante
5. Exporte 3 fichiers CSV dans `consolidated_results/` :
   - `consolidated_results_detailed.csv` : Résultats détaillés par police et cédante
   - `consolidated_results_by_policy.csv` : Agrégation par police
   - `statistics_by_cedant.csv` : Statistiques par cédante

## Développement

### Formatage du code avec Black

Le projet utilise [Black](https://black.readthedocs.io/) pour le formatage automatique du code Python.

```bash
# Vérifier quels fichiers nécessitent un formatage
uv run black --check .

# Formater tous les fichiers Python du projet
uv run black .

# Formater un fichier ou dossier spécifique
uv run black path/to/file.py
uv run black structures/
```

La configuration de Black se trouve dans le fichier `pyproject.toml`.

## Exemples et Démonstrations

Le dossier `examples/` contient tous les exemples organisés par catégorie :

### Tests rapides
```bash
# Test des programmes simples
uv run python test_simple_programs.py

# Test de la logique claim_basis
uv run python examples/scripts/example_claim_basis_usage.py

# Démonstration de l'organisation
uv run python demo_organized_examples.py
```

### Structure des exemples
- **`examples/bordereaux/`** : Exemples de bordereaux organisés par ligne de business (aviation/, test/)
  - Consultez [examples/bordereaux/README.md](examples/bordereaux/README.md) pour les conventions
- **`examples/programs/`** : Programmes simples (séquentiel/parallèle)
- **`examples/scripts/`** : Scripts de démonstration et d'exemple

Consultez [examples/README.md](examples/README.md) pour plus de détails.

### Créer une nouvelle configuration

**Option 1 : Avec Cursor/LLM**
Utilisez le fichier `PROGRAM_SPECIFICATION_GUIDE.md` comme référence. Décrivez simplement ce que vous voulez en langage naturel, et Cursor générera automatiquement le code Python pour créer la configuration.

Exemple :
```
"Crée un programme avec une quota-share de 30% par défaut et 40% pour Paris,
suivi d'un XoL de 1M xs 500K uniquement pour Paris"
```

**Option 2 : Script Python**
Le script `create_program_config.py` montre comment créer un fichier de configuration programmatiquement. 
Vous pouvez le modifier pour créer vos propres programmes.

**Option 3 : CSV direct**
Éditez directement les fichiers CSV dans le dossier `program_config/`.

## Exemple de résultat

**PROGRAM_2024 (sequential)** avec 2 structures :

### Structure QS_GENERAL (quota_share)
- condition 1 : 30% sans condition (défaut)
- condition 2 : 40% pour localisation=Paris (spécifique)

### Structure XOL_LARGE (excess_of_loss)
- condition 1 : 1M xs 500K pour localisation=Paris

### Application sur les polices

**Police POL-2024-001 (France, EMEA, Construction, 500K€)**
1. **QS_GENERAL** ✓ condition matchée : country=France (40%)
   - 500K€ × 40% = **200K€ cédés**
2. **XOL_LARGE** ✓ condition matchée : country=France
   - Sur 300K€ restants, 0€ cédé (sous la priorité de 500K)

**Total : 200K€ cédés, 300K€ retenus**

**Police POL-2024-002 (France, EMEA, Technology, 750K€)**
1. **QS_GENERAL** ✓ condition matchée : country=France (40%)
   - 750K€ × 40% = **300K€ cédés**
2. **XOL_LARGE** ✓ condition matchée : country=France
   - Sur 450K€ restants, 0€ cédé (sous la priorité de 500K)

**Total : 300K€ cédés, 450K€ retenus**

**Police POL-2024-003 (Singapore, APAC, Manufacturing, 1.2M€)**
1. **QS_GENERAL** ✓ condition matchée : All (no conditions) (30%)
   - 1.2M€ × 30% = **360K€ cédés**
2. **XOL_LARGE** ✗ Aucune condition ne matche

**Total : 360K€ cédés, 840K€ retenus**

## Avantages du modèle conditions

1. **Flexibilité** : Une même structure peut avoir des paramètres différents selon les conditions
2. **Simplicité** : Pas besoin de créer des structures différentes pour chaque variation
3. **Priorité automatique** : Le système choisit automatiquement la condition la plus spécifique
4. **Extensibilité** : Ajout facile de nouvelles dimensions sans changer le code
5. **Modèle relationnel** : Plus proche d'une base de données relationnelle classique

## Création de programmes avec Cursor

Le fichier `PROGRAM_SPECIFICATION_GUIDE.md` contient la spécification complète du format de données et des exemples de traduction.

**Comment l'utiliser :**
1. Ouvrez le fichier `PROGRAM_SPECIFICATION_GUIDE.md`
2. Décrivez votre besoin en langage naturel à Cursor
3. Cursor utilisera automatiquement le guide pour générer le code Python correct
4. Exécutez le script généré pour créer votre dossier CSV

**Exemples de demandes :**
- "Crée un programme avec 25% de cession par défaut, 30% pour la France et 35% pour EMEA"
- "Je veux un XoL de 800K xs 400K qui s'applique uniquement aux industries de technologie"
- "Programme en parallèle : 20% quota-share + XoL 500K xs 300K sur toutes les polices"
- "30% pour Property, 35% pour Commercial Property, 40% pour Commercial Fire"

Le guide contient des patterns courants, des exemples de traduction et toutes les règles de validation.

## Nomenclature

- **Program** : Le programme global (un par fichier)
- **Structure** : Un élément du programme utilisant un produit de base
- **condition** : Instance d'une structure avec paramètres et conditions spécifiques
- **Product** : Les building blocks (quota_share, excess_of_loss)
- **Dimension** : Colonne du bordereau utilisée pour le matching (ex: country, region, industry)
- **cession rate** : Le taux de cession pour une quota-share


# Helpers

./snowflake-cli reset-tables --force

uv run python examples/program_creation/create_aviation_old_republic.py