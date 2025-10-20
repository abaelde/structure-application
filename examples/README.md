# Exemples et Démonstrations

Ce dossier contient tous les exemples, fichiers de test et démonstrations du système de structures de réassurance.

## Structure des dossiers

### 📊 `bordereaux/`
Contient les exemples de bordereaux (fichiers CSV) avec différentes configurations :

- **`bordereau_exemple.csv`** : Bordereau de base avec les nouveaux champs `inception_date` et `expiry_date`
- **`bordereau_multi_year_test.csv`** : Bordereau de test pour démontrer la logique claim_basis avec des polices de différentes années

### 🏗️ `programs/`
Contient les exemples de programmes de réassurance (dossiers CSV) :

### 📋 `treaties/`
Contient les traités multi-années pour démontrer la logique claim_basis :


### 🔧 `scripts/`
Contient les scripts de démonstration et d'exemple :

- **`create_simple_programs.py`** : Script pour créer les programmes simples (séquentiel et parallèle)
- **`create_program_config.py`** : Script pour créer un fichier de configuration d'exemple
- **`example_claim_basis_usage.py`** : Exemple d'utilisation de la logique claim_basis
- **`apply_program_with_mapping.py`** : Script pour appliquer automatiquement les programmes à leurs bordereaux mappés

### 🔗 `program_bordereau_mapping.py`
Fichier de configuration définissant la correspondance entre programmes et bordereaux.

Ce fichier centralise tous les mappings programme-bordereau pour faciliter :
- L'exécution automatisée des tests
- La gestion des correspondances programme-bordereau
- L'identification des bordereaux manquants

## Utilisation des exemples

### 1. Vérifier le statut des mappings programme-bordereau
```bash
# Afficher le statut de tous les mappings
uv run python examples/program_bordereau_mapping.py

# Ou via le script d'application
uv run python examples/scripts/apply_program_with_mapping.py --status
```

### 2. Appliquer un programme à son bordereau mappé
```bash
# Appliquer un programme spécifique
uv run python examples/scripts/apply_program_with_mapping.py aviation_axa_xl_2024

# Appliquer tous les programmes prêts
uv run python examples/scripts/apply_program_with_mapping.py --all
```

### 3. Test des programmes simples
```bash
# Depuis la racine du projet
uv run python test_simple_programs.py
```

### 4. Test de la logique claim_basis
```bash
# Depuis la racine du projet
uv run python examples/scripts/example_claim_basis_usage.py
```

### 5. Création de nouveaux programmes
```bash
# Depuis la racine du projet
uv run python examples/scripts/create_simple_programs.py
```

### 6. Création d'un fichier de configuration
```bash
# Depuis la racine du projet
uv run python examples/scripts/create_program_config.py
```

## Structure des bordereaux CSV

Colonnes requises :
- `policy_id` : Numéro de la police
- `exposure` : Montant de l'exposure
- `inception_date` : Date de souscription
- `expiry_date` : Date d'expiration
- Colonnes de dimensions pour le matching

## Mapping Programme-Bordereau

Le fichier `program_bordereau_mapping.py` centralise les correspondances entre les programmes et leurs bordereaux de test.

### État actuel des mappings

- ✅ **aviation_axa_xl_2024** → `bordereau_aviation_axa_xl.csv` (READY)
- ⚠️  **aviation_old_republic_2024** → TODO: créer bordereau
- ⚠️  **casualty_aig_2024** → TODO: créer bordereau
- ⚠️  **single_excess_of_loss** → TODO: créer bordereau
- ⚠️  **single_quota_share** → TODO: créer bordereau

### Ajouter un nouveau mapping

Pour ajouter un nouveau mapping, modifiez le dictionnaire `PROGRAM_BORDEREAU_MAPPING` dans `program_bordereau_mapping.py` :

```python
PROGRAM_BORDEREAU_MAPPING = {
    "aviation_axa_xl_2024": "bordereau_aviation_axa_xl",
    "mon_nouveau_programme": "mon_nouveau_bordereau",  # Ajouter ici
}
```

### Fonctions utilitaires disponibles

```python
from examples.program_bordereau_mapping import (
    get_mapped_bordereau,      # Obtenir le bordereau d'un programme
    get_ready_pairs,            # Obtenir les paires prêtes
    get_missing_bordereaux,     # Lister les bordereaux manquants
    display_mapping_status,     # Afficher le statut des mappings
)
```

## Notes importantes

1. **Compatibilité** : Tous les exemples sont compatibles avec la version actuelle du système
2. **Tests** : Les fichiers de test peuvent être modifiés pour tester de nouveaux scénarios
3. **Évolutivité** : La structure permet d'ajouter facilement de nouveaux exemples
4. **Documentation** : Chaque exemple est documenté dans les scripts correspondants
5. **Mappings** : Chaque programme devrait avoir un bordereau correspondant pour faciliter les tests
