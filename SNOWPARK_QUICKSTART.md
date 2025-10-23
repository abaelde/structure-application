# 🚀 Snowpark Quick Start Guide

Ce guide vous permet de démarrer rapidement avec les procédures Snowpark pour la lecture de programmes de réassurance.

## 📋 Prérequis

1. **Configuration Snowflake** : Le fichier `snowflake_config.env` doit être configuré
2. **Dépendances** : `snowflake-snowpark-python` est déjà installé dans le projet
3. **Données** : Des programmes doivent exister dans votre base Snowflake

## 🚀 Démarrage Rapide

### 1. Test de connexion rapide

```bash
# Test simple de la connexion Snowpark
uv run python scripts/test_snowpark_simple.py
```

### 2. Tests complets

```bash
# Tests détaillés de toutes les fonctionnalités
uv run python scripts/test_simple_procedures.py
```

## 📚 Utilisation en Python

### Connexion et session

```python
from snowflake_utils import get_snowpark_session, close_snowpark_session

# Obtenir une session Snowpark
session = get_snowpark_session()

# Votre code ici...

# Fermer la session
close_snowpark_session()
```

### Lecture de programmes

```python
from snowflake_utils import read_program_via_snowpark

# Lire un programme complet
program_data = read_program_via_snowpark(session, program_id=1)

# Les données sont retournées sous forme de dictionnaire
program = program_data["program"][0]  # Premier (et seul) programme
structures = program_data["structures"]
conditions = program_data["conditions"]
exclusions = program_data["exclusions"]
field_links = program_data["field_links"]

print(f"Programme: {program['TITLE']}")
print(f"Structures: {len(structures)}")
print(f"Conditions: {len(conditions)}")
```

### Liste des programmes

```python
from snowflake_utils import list_programs_via_snowpark

# Lister tous les programmes
programs_data = list_programs_via_snowpark(session)

programs = programs_data["programs"]
total_count = programs_data["total_count"]

print(f"Total: {total_count} programmes")
for program in programs:
    print(f"- {program['TITLE']} (ID: {program['REINSURANCE_PROGRAM_ID']})")
```

### Vérification d'existence

```python
from snowflake_utils import program_exists_via_snowpark

# Vérifier si un programme existe
exists = program_exists_via_snowpark(session, program_id=1)
print(f"Programme 1 existe: {exists}")
```

## 🔧 Fonctions Disponibles

### `read_program_via_snowpark(session, program_id: int) -> dict`

Lit un programme complet avec toutes ses données associées.

**Paramètres :**
- `session` : Session Snowpark active
- `program_id` : ID du programme à lire

**Retour :**
- Dictionnaire contenant :
  - `program` : Données du programme principal
  - `structures` : Structures de réassurance
  - `conditions` : Conditions d'application
  - `exclusions` : Exclusions globales
  - `field_links` : Overrides de champs
  - `metadata` : Métadonnées (compteurs, etc.)

### `list_programs_via_snowpark(session) -> dict`

Liste tous les programmes disponibles avec leurs métadonnées.

**Paramètres :**
- `session` : Session Snowpark active

**Retour :**
- Dictionnaire contenant :
  - `programs` : Liste des programmes
  - `total_count` : Nombre total de programmes

### `program_exists_via_snowpark(session, program_id: int) -> bool`

Vérifie si un programme existe.

**Paramètres :**
- `session` : Session Snowpark active
- `program_id` : ID du programme à vérifier

**Retour :**
- `True` si le programme existe, `False` sinon

## 🐛 Dépannage

### Erreur de connexion

```
❌ Échec de la connexion Snowpark: ...
```

**Solutions :**
1. Vérifiez votre fichier `snowflake_config.env`
2. Testez la connexion classique : `uv run python -c "from snowflake_utils import test_connection; test_connection()"`
3. Vérifiez vos permissions Snowflake

### Erreur de session

```
❌ Échec de la connexion Snowpark: ...
```

**Solutions :**
1. Vérifiez votre fichier `snowflake_config.env`
2. Testez la connexion classique : `uv run python -c "from snowflake_utils import test_connection; test_connection()"`
3. Vérifiez vos permissions Snowflake

### Fonction non trouvée

```
❌ Erreur: Module 'simple_procedures' not found
```

**Solutions :**
1. Vérifiez que le fichier `snowflake_utils/simple_procedures.py` existe
2. Vérifiez que les imports sont corrects dans votre code

## 📊 Comparaison avec l'approche classique

| Aspect | Snowflake Classique | Snowpark |
|--------|-------------------|----------|
| **Connexion** | `snowflake.connector.connect()` | `Session.builder.create()` |
| **Requêtes** | SQL brut avec cursors | DataFrames Snowpark |
| **Exécution** | Côté client | Côté serveur |
| **Performance** | Transfert de données | Traitement distribué |
| **Maintenance** | Code dispersé | Procédures centralisées |

## 🎯 Prochaines Étapes

1. **Tester** les procédures de lecture avec vos données
2. **Implémenter** les procédures d'écriture
3. **Créer** les procédures d'application de programmes
4. **Migrer** progressivement votre code existant

## 📞 Support

En cas de problème :

1. Consultez les logs détaillés des scripts de test
2. Vérifiez la configuration Snowflake
3. Testez d'abord avec le script `quick_snowpark_test.py`
4. Consultez la documentation Snowpark officielle

---

*Ce guide sera mis à jour au fur et à mesure de l'ajout de nouvelles fonctionnalités Snowpark.*
