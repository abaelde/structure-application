# Reinsurance Program Application System

Système d'application de programmes de réassurance sur des bordereaux.

## Architecture

### Structure du projet

```
structure-application/
├── products/                           # Building blocks de réassurance
│   ├── base_products.py               # quota_share & excess_of_loss
│   └── __init__.py
├── structures/                         # Moteur d'application des programmes
│   ├── structure_loader.py            # Chargement depuis Excel (ProgramLoader)
│   ├── structure_engine.py            # Logique d'application et matching de sections
│   ├── treaty_manager.py              # Gestionnaire de traités multi-années
│   ├── program_display.py             # Affichage des programmes
│   └── __init__.py
├── examples/                           # Exemples et démonstrations
│   ├── README.md                      # Documentation des exemples
│   ├── bordereaux/                    # Exemples de bordereaux
│   │   ├── bordereau_exemple.csv      # Bordereau de base
│   │   └── bordereau_multi_year_test.csv # Test claim_basis
│   ├── programs/                      # Exemples de programmes
│   │   ├── program_simple_sequential.xlsx
│   │   ├── program_simple_parallel.xlsx
│   │   └── program_simple_*_updated.xlsx
│   ├── treaties/                      # Traités multi-années
│   │   ├── treaty_2023.xlsx
│   │   ├── treaty_2024.xlsx
│   │   └── treaty_2025.xlsx
│   └── scripts/                       # Scripts d'exemple
│       ├── create_simple_programs.py
│       ├── create_program_config.py
│       └── example_claim_basis_usage.py
├── program_config.xlsx                # Configuration du programme (Excel)
├── PROGRAM_SPECIFICATION_GUIDE.md     # Guide de spécification des programmes
├── CLAIM_BASIS_GUIDE.md               # Guide de la logique claim_basis
├── main.py                            # Point d'entrée principal
├── test_simple_programs.py            # Tests des programmes simples
├── test_new_fields.py                 # Tests des nouveaux champs
├── demo_organized_examples.py         # Démonstration de l'organisation
└── README.md                          # Documentation
```

## Concepts

### 1. Bordereau
Fichier CSV contenant les polices d'assurance avec :
- `numero_police` : Identifiant unique
- `nom_assure` : Nom de l'assuré
- `country` : Pays
- `region` : Région (APAC, EMEA, Americas, etc.)
- `product_type_1`, `product_type_2`, `product_type_3` : Hiérarchie des types de produits
- `currency` : Devise
- `line_of_business` : Ligne de business
- `industry` : Industrie
- `sic_code` : Code SIC
- `include` : Champ libre pour conditions spéciales
- `exposition` : Valeur d'exposition
- `inception_date` : Date de souscription de la police
- `expiry_date` : Date d'expiration de la police

### 2. Produits de base
- **quota-share** : Application d'un pourcentage de cession (cession_PCT) sur l'exposition
- **Excess of Loss (XoL)** : Couverture au-dessus d'une priorité (attachment_point_100) jusqu'à une limite (limit_occurrence_100)

### 3. Program
Un fichier de configuration contient **un seul programme** qui est constitué de **plusieurs structures**.

Le programme définit :
- **Nom** : Identifiant du programme
- **Mode** : Comment les structures s'appliquent
  - `sequential` : Les structures s'appliquent successivement (la sortie de l'une devient l'entrée de la suivante)
  - `parallel` : Chaque structure s'applique indépendamment sur l'exposition initiale

### 4. Structures
Les structures sont les éléments qui composent un programme. Chaque structure :
- Est définie par son nom, son ordre d'application et le type de produit utilisé
- Possède plusieurs **sections** qui définissent les paramètres et conditions d'application
- Peut avoir un **claim_basis** : "risk_attaching" ou "loss_occurring"
- A des dates de validité : `inception_date` et `expiry_date`

### 5. Sections
Les sections sont les instanciations concrètes d'une structure avec :
- **Paramètres** : cession_PCT (pour quota_share), attachment_point_100 et limit_occurrence_100 (pour excess_of_loss)
- **Conditions** : Valeurs spécifiques pour les dimensions (localisation, industrie, etc.)

#### Logique de matching
Pour chaque police et chaque structure :
1. Le système cherche toutes les sections dont les conditions matchent la police
2. Si plusieurs sections matchent, la **plus spécifique** est choisie (celle avec le plus de conditions)
3. Si aucune section ne matche, la structure n'est pas appliquée

**Exemple :**
- Section 1 : cession_PCT=30%, localisation=NULL → S'applique partout (générique)
- Section 2 : cession_PCT=40%, localisation=Paris → S'applique uniquement à Paris (spécifique)

Pour une police à Paris, la Section 2 sera choisie car elle est plus spécifique.

## Logique Claim Basis

Le système implémente la logique **claim_basis** qui détermine quel traité appliquer selon la date de la loss et la date de souscription de la police.

### Types de Claim Basis

#### `risk_attaching`
- **Règle** : Utilise le traité qui était en vigueur lors de la **souscription** de la police
- **Date de référence** : `inception_date` de la police
- **Exemple** : Police souscrite en 2023 → Applique le traité de 2023, même si la loss survient en 2025

#### `loss_occurring`
- **Règle** : Utilise le traité qui est en vigueur au moment de la **loss**
- **Date de référence** : Date de calcul "as of now"
- **Exemple** : Loss en 2025 → Applique le traité de 2025, même si la police a été souscrite en 2023

### Utilisation avec TreatyManager

```python
from structures.treaty_manager import TreatyManager
from structures.structure_engine import apply_treaty_manager_to_bordereau

# Charger les traités multi-années
treaty_paths = {
    "2023": "examples/treaties/treaty_2023.xlsx",
    "2024": "examples/treaties/treaty_2024.xlsx", 
    "2025": "examples/treaties/treaty_2025.xlsx"
}

treaty_manager = TreatyManager(treaty_paths)

# Calcul "as of now"
results = apply_treaty_manager_to_bordereau(
    bordereau_df, treaty_manager, "2025-06-15"
)
```

Pour plus de détails, consultez le [Guide Claim Basis](CLAIM_BASIS_GUIDE.md).

## Configuration Excel

Le fichier `program_config.xlsx` contient 3 feuilles :

### Feuille "program"
Définit le programme principal (une seule ligne).

| program_name | mode       |
|--------------|------------|
| PROGRAM_2024 | sequential |

### Feuille "structures"
Définit les structures du programme (nom, ordre, type de produit).

| structure_name | contract_order | type_of_participation    |
|----------------|-------|-----------------|
| QS_GENERAL     | 1     | quota_share     |
| XOL_LARGE      | 2     | excess_of_loss  |

### Feuille "sections"
Définit les sections de chaque structure avec paramètres et conditions.

| structure_name | cession_PCT | attachment_point_100 | limit_occurrence_100   | localisation | industrie |
|----------------|--------------|----------|---------|--------------|-----------|
| QS_GENERAL     | 0.30         | -        | -       | -            | -         |
| QS_GENERAL     | 0.40         | -        | -       | Paris        | -         |
| XOL_LARGE      | -            | 500000   | 1000000 | Paris        | -         |

**Notes importantes :**
- Les colonnes de dimensions (localisation, industrie) sont détectées automatiquement
- Une valeur vide (NaN) dans une colonne de dimension signifie "pas de condition sur cette dimension"
- Plusieurs sections peuvent exister pour la même structure avec différentes combinaisons de conditions
- Le système choisit automatiquement la section la plus spécifique (avec le plus de conditions matchées)

## Utilisation

```bash
# Installer les dépendances
uv sync

# Créer/recréer le fichier de configuration (optionnel)
uv run python examples/scripts/create_program_config.py

# Exécuter le système
uv run python main.py
```

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
- **`examples/bordereaux/`** : Exemples de bordereaux avec les nouveaux champs
- **`examples/programs/`** : Programmes simples (séquentiel/parallèle)
- **`examples/treaties/`** : Traités multi-années pour claim_basis
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

**Option 3 : Excel direct**
Éditez directement le fichier Excel `program_config.xlsx`.

## Exemple de résultat

**PROGRAM_2024 (sequential)** avec 2 structures :

### Structure QS_GENERAL (quota_share)
- Section 1 : 30% sans condition (défaut)
- Section 2 : 40% pour localisation=Paris (spécifique)

### Structure XOL_LARGE (excess_of_loss)
- Section 1 : 1M xs 500K pour localisation=Paris

### Application sur les polices

**Police POL-2024-001 (France, EMEA, Construction, 500K€)**
1. **QS_GENERAL** ✓ Section matchée : country=France (40%)
   - 500K€ × 40% = **200K€ cédés**
2. **XOL_LARGE** ✓ Section matchée : country=France
   - Sur 300K€ restants, 0€ cédé (sous la priorité de 500K)

**Total : 200K€ cédés, 300K€ retenus**

**Police POL-2024-002 (France, EMEA, Technology, 750K€)**
1. **QS_GENERAL** ✓ Section matchée : country=France (40%)
   - 750K€ × 40% = **300K€ cédés**
2. **XOL_LARGE** ✓ Section matchée : country=France
   - Sur 450K€ restants, 0€ cédé (sous la priorité de 500K)

**Total : 300K€ cédés, 450K€ retenus**

**Police POL-2024-003 (Singapore, APAC, Manufacturing, 1.2M€)**
1. **QS_GENERAL** ✓ Section matchée : All (no conditions) (30%)
   - 1.2M€ × 30% = **360K€ cédés**
2. **XOL_LARGE** ✗ Aucune section ne matche

**Total : 360K€ cédés, 840K€ retenus**

## Avantages du modèle Sections

1. **Flexibilité** : Une même structure peut avoir des paramètres différents selon les conditions
2. **Simplicité** : Pas besoin de créer des structures différentes pour chaque variation
3. **Priorité automatique** : Le système choisit automatiquement la section la plus spécifique
4. **Extensibilité** : Ajout facile de nouvelles dimensions sans changer le code
5. **Modèle relationnel** : Plus proche d'une base de données relationnelle classique

## Création de programmes avec Cursor

Le fichier `PROGRAM_SPECIFICATION_GUIDE.md` contient la spécification complète du format de données et des exemples de traduction.

**Comment l'utiliser :**
1. Ouvrez le fichier `PROGRAM_SPECIFICATION_GUIDE.md`
2. Décrivez votre besoin en langage naturel à Cursor
3. Cursor utilisera automatiquement le guide pour générer le code Python correct
4. Exécutez le script généré pour créer votre fichier Excel

**Exemples de demandes :**
- "Crée un programme avec 25% de cession par défaut, 30% pour la France et 35% pour EMEA"
- "Je veux un XoL de 800K xs 400K qui s'applique uniquement aux industries de technologie"
- "Programme en parallèle : 20% quota-share + XoL 500K xs 300K sur toutes les polices"
- "30% pour Property, 35% pour Commercial Property, 40% pour Commercial Fire"

Le guide contient des patterns courants, des exemples de traduction et toutes les règles de validation.

## Nomenclature

- **Program** : Le programme global (un par fichier)
- **Structure** : Un élément du programme utilisant un produit de base
- **Section** : Instance d'une structure avec paramètres et conditions spécifiques
- **Product** : Les building blocks (quota_share, excess_of_loss)
- **Dimension** : Colonne du bordereau utilisée pour le matching (ex: country, region, industry)
- **cession rate** : Le taux de cession pour une quota-share
