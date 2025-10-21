# Intégration Snowflake

Cette documentation décrit l'intégration Snowflake pour le système de réassurance, implémentée avec une approche pragmatique utilisant le modèle **payload JSON**.

## 🎯 Objectifs

- **Intégration rapide** : Pas de migration de schéma à chaque ajout de champ
- **Évolutivité** : Modèle flexible qui s'adapte aux changements
- **Performance** : Colonnes scalaires pour les clés, JSON pour le reste
- **Simplicité** : Réutilisation du code existant sans modification majeure

## 🏗️ Architecture

### Modèle de données

Le système utilise **4 tables principales** pour les programmes :

1. **PROGRAMS** - Métadonnées des programmes
2. **STRUCTURES** - Structures de réassurance
3. **CONDITIONS** - Conditions par structure
4. **EXCLUSIONS** - Exclusions par programme

Et **3 tables** pour les runs :

1. **RUNS** - Métadonnées des exécutions
2. **RUN_POLICIES** - Politiques traitées
3. **RUN_POLICY_STRUCTURES** - Structures appliquées

### Stratégie payload JSON

- **Colonnes scalaires** : Clés de jointure, dates, types de participation, etc.
- **Colonne PAYLOAD** : JSON contenant tous les champs "non-stables"
- **Avantage** : Évolution du schéma sans migration DDL

## 🚀 Installation

### 1. Prérequis

```bash
# Installer le connecteur Snowflake
uv add snowflake-connector-python
```

### 2. Configuration

Copiez le fichier de configuration :

```bash
cp snowflake_config.example snowflake_config.env
```

Éditez `snowflake_config.env` avec vos paramètres :

```bash
SNOWFLAKE_ACCOUNT=your_account.snowflakecomputing.com
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=MYDB
SNOWFLAKE_SCHEMA=MYSCHEMA
SNOWFLAKE_ROLE=your_role
```

### 3. Création des tables

Exécutez le script SQL dans votre instance Snowflake :

```bash
# Via l'interface Snowflake ou snowsql
snowsql -c your_connection -f scripts/setup_snowflake_tables.sql
```

## 📖 Utilisation

### Programmes

#### Charger un programme depuis Snowflake

```python
from src.managers import ProgramManager

# Configuration
connection_params = {
    "account": "your_account",
    "user": "your_user", 
    "password": "your_password",
    "warehouse": "your_warehouse",
    "database": "MYDB",
    "schema": "MYSCHEMA",
    "role": "your_role"
}

# Charger
pm = ProgramManager(backend="snowflake")
program = pm.load(
    "snowflake://MYDB.MYSCHEMA?program_title=Mon Programme",
    io_kwargs={"connection_params": connection_params}
)
```

#### Sauvegarder un programme dans Snowflake

```python
# Sauvegarder
pm.save(
    program, 
    "snowflake://MYDB.MYSCHEMA?program_title=Mon Programme",
    io_kwargs={
        "connection_params": connection_params,
        "if_exists": "replace_program"  # ou "append", "truncate_all"
    }
)
```

### Runs

#### Sauvegarder un run

```python
from src.io import RunSnowflakeIO

run_io = RunSnowflakeIO()
run_io.write(
    "snowflake://MYDB.MYSCHEMA",
    runs_df,
    run_policies_df, 
    run_policy_structures_df,
    connection_params=connection_params
)
```

#### Charger des runs

```python
runs, policies, structures = run_io.read(
    "snowflake://MYDB.MYSCHEMA",
    connection_params=connection_params
)
```

### Bordereaux

Le système existant `SnowflakeBordereauIO` fonctionne déjà :

```python
from src.io import SnowflakeBordereauIO

bordereau_io = SnowflakeBordereauIO()
bordereau = bordereau_io.read(
    "snowflake://MYDB.MYSCHEMA.MY_BORDEREAU_TABLE",
    connection_params=connection_params
)
```

## 🔧 Modes d'écriture

### `if_exists` pour les programmes

- **`"append"`** : Ajoute un nouveau PROGRAM_ID
- **`"replace_program"`** : Supprime le programme existant (même titre) puis ré-insère
- **`"truncate_all"`** : TRUNCATE des 4 tables avant insert (reset global)

## 🛠️ Opérations d'administration

### Reset complet

```python
from src.io import SnowflakeProgramIO, RunSnowflakeIO

# Reset des programmes
program_io = SnowflakeProgramIO()
program_io.drop_all_tables(
    "snowflake://MYDB.MYSCHEMA",
    connection_params=connection_params
)

# Reset des runs
run_io = RunSnowflakeIO()
run_io.drop_all_tables(
    "snowflake://MYDB.MYSCHEMA", 
    connection_params=connection_params
)
```

### Tronquer les tables

```python
# Via le mode truncate_all
pm.save(program, dsn, io_kwargs={
    "connection_params": connection_params,
    "if_exists": "truncate_all"
})
```

## 🧪 Tests

Exécutez l'exemple d'intégration :

```bash
# Configurer les variables d'environnement
export SNOWFLAKE_ACCOUNT=your_account
export SNOWFLAKE_USER=your_user
# ... etc

# Exécuter l'exemple
uv run python examples/snowflake_integration_example.py
```

## 📊 Vues analytiques

Le script SQL crée des vues utiles :

- **`V_PROGRAMS_DETAILED`** : Extraction de champs du payload JSON
- **`V_RUN_STATISTICS`** : Statistiques agrégées des runs

Exemple d'utilisation :

```sql
-- Statistiques par programme
SELECT 
  PROGRAM_NAME,
  COUNT(*) as RUN_COUNT,
  SUM(TOTAL_EXPOSURE) as TOTAL_EXPOSURE,
  AVG(TOTAL_CESSION) as AVG_CESSION
FROM MYDB.MYSCHEMA.V_RUN_STATISTICS
GROUP BY PROGRAM_NAME;
```

## 🔍 DSN (Data Source Names)

### Format général

```
snowflake://DATABASE.SCHEMA[?param1=value1&param2=value2]
```

### Exemples

- **Programme par titre** : `snowflake://MYDB.MYSCHEMA?program_title=Aviation AXA XL`
- **Programme par ID** : `snowflake://MYDB.MYSCHEMA?program_id=abc123`
- **Runs** : `snowflake://MYDB.MYSCHEMA`
- **Bordereau** : `snowflake://MYDB.MYSCHEMA.BORDEREAU_TABLE`

## ⚡ Performance

### Index créés automatiquement

- `IDX_PROGRAMS_TITLE` sur `PROGRAMS(TITLE)`
- `IDX_STRUCTURES_PROGRAM` sur `STRUCTURES(PROGRAM_ID)`
- `IDX_CONDITIONS_PROGRAM` sur `CONDITIONS(PROGRAM_ID)`
- Etc.

### Optimisations recommandées

1. **Clustering** sur les tables volumineuses
2. **Partitioning** par date si applicable
3. **Warehouse sizing** selon la charge

## 🚨 Limitations et considérations

### Sécurité

- **Mots de passe** : Utilisez des secrets managers en production
- **Permissions** : Principe du moindre privilège
- **Chiffrement** : Snowflake chiffre par défaut

### Performance

- **Payload JSON** : Plus volumineux que des colonnes natives
- **Parsing** : Coût CPU pour extraire des champs du JSON
- **Index** : Impossible d'indexer directement le contenu JSON

### Évolutivité

- **Taille des payloads** : Limite de 16MB par ligne Snowflake
- **Complexité JSON** : Éviter les structures trop imbriquées
- **Migration** : Possible de migrer vers colonnes natives plus tard

## 🔄 Migration depuis CSV

### Script de migration

```python
from src.managers import ProgramManager

# Charger depuis CSV
pm_csv = ProgramManager(backend="csv_folder")
program = pm_csv.load("examples/programs/aviation_axa_xl_2024")

# Sauvegarder dans Snowflake
pm_snowflake = ProgramManager(backend="snowflake")
pm_snowflake.save(
    program,
    "snowflake://MYDB.MYSCHEMA?program_title=Aviation AXA XL",
    io_kwargs={"connection_params": connection_params}
)
```

## 📚 Ressources

- [Documentation Snowflake Connector](https://docs.snowflake.com/en/user-guide/python-connector.html)
- [Snowflake SQL Reference](https://docs.snowflake.com/en/sql-reference.html)
- [Exemple d'intégration](examples/snowflake_integration_example.py)
- [Script de création des tables](scripts/setup_snowflake_tables.sql)
