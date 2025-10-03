# Exemples et Démonstrations

Ce dossier contient tous les exemples, fichiers de test et démonstrations du système de structures de réassurance.

## Structure des dossiers

### 📊 `bordereaux/`
Contient les exemples de bordereaux (fichiers CSV) avec différentes configurations :

- **`bordereau_exemple.csv`** : Bordereau de base avec les nouveaux champs `inception_date` et `expiry_date`
- **`bordereau_multi_year_test.csv`** : Bordereau de test pour démontrer la logique claim_basis avec des polices de différentes années

### 🏗️ `programs/`
Contient les exemples de programmes de réassurance (fichiers Excel) :

- **`program_simple_sequential.xlsx`** : Programme séquentiel mis à jour avec les nouveaux champs
- **`program_simple_parallel.xlsx`** : Programme parallèle mis à jour avec les nouveaux champs
- **`program_simple_sequential_updated.xlsx`** : Version mise à jour du programme séquentiel
- **`program_simple_parallel_updated.xlsx`** : Version mise à jour du programme parallèle

### 📋 `treaties/`
Contient les traités multi-années pour démontrer la logique claim_basis :

- **`treaty_2023.xlsx`** : Traité 2023 (QS 25% + XOL 800K xs 400K)
- **`treaty_2024.xlsx`** : Traité 2024 (QS 30% + XOL 1M xs 500K)
- **`treaty_2025.xlsx`** : Traité 2025 (QS 35% + XOL 1.2M xs 600K)

### 🔧 `scripts/`
Contient les scripts de démonstration et d'exemple :

- **`create_simple_programs.py`** : Script pour créer les programmes simples (séquentiel et parallèle)
- **`create_program_config.py`** : Script pour créer un fichier de configuration d'exemple
- **`example_claim_basis_usage.py`** : Exemple d'utilisation de la logique claim_basis

## Utilisation des exemples

### 1. Test des programmes simples
```bash
# Depuis la racine du projet
uv run python test_simple_programs.py
```

### 2. Test de la logique claim_basis
```bash
# Depuis la racine du projet
uv run python examples/scripts/example_claim_basis_usage.py
```

### 3. Création de nouveaux programmes
```bash
# Depuis la racine du projet
uv run python examples/scripts/create_simple_programs.py
```

### 4. Création d'un fichier de configuration
```bash
# Depuis la racine du projet
uv run python examples/scripts/create_program_config.py
```

## Structure des fichiers Excel

### Feuille "program"
- `program_name` : Nom du programme
- `mode` : "sequential" ou "parallel"

### Feuille "structures"
- `structure_name` : Nom de la structure
- `order` : Ordre d'application
- `product_type` : "quote_share" ou "excess_of_loss"
- `claim_basis` : "risk_attaching" ou "loss_occurring"
- `inception_date` : Date de début de la structure
- `expiry_date` : Date de fin de la structure

### Feuille "sections"
- `structure_name` : Référence vers la structure
- `cession_rate` : Taux de cession (pour quote_share)
- `priority` : Priorité (pour excess_of_loss)
- `limit` : Limite (pour excess_of_loss)
- Colonnes de dimensions pour le matching

## Structure des bordereaux CSV

Colonnes requises :
- `numero_police` : Numéro de la police
- `exposition` : Montant de l'exposition
- `inception_date` : Date de souscription
- `expiry_date` : Date d'expiration
- Colonnes de dimensions pour le matching

## Notes importantes

1. **Compatibilité** : Tous les exemples sont compatibles avec la version actuelle du système
2. **Tests** : Les fichiers de test peuvent être modifiés pour tester de nouveaux scénarios
3. **Évolutivité** : La structure permet d'ajouter facilement de nouveaux exemples
4. **Documentation** : Chaque exemple est documenté dans les scripts correspondants
