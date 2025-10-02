# Guide de la logique Claim Basis

## Vue d'ensemble

Le système implémente maintenant la logique **claim_basis** qui détermine quel traité appliquer selon la date de la loss et la date de souscription de la police.

## Types de Claim Basis

### 1. `risk_attaching`
- **Règle** : Utilise le traité qui était en vigueur lors de la **souscription** de la police
- **Date de référence** : `inception_date` de la police
- **Exemple** : Police souscrite en 2023 → Applique le traité de 2023, même si la loss survient en 2025

### 2. `loss_occurring`
- **Règle** : Utilise le traité qui est en vigueur au moment de la **loss**
- **Date de référence** : Date de calcul "as of now"
- **Exemple** : Loss en 2025 → Applique le traité de 2025, même si la police a été souscrite en 2023

## Utilisation

### 1. Charger les traités multi-années

```python
from structures.treaty_manager import TreatyManager

# Définir les chemins vers les traités par année
treaty_paths = {
    "2023": "treaty_2023.xlsx",
    "2024": "treaty_2024.xlsx", 
    "2025": "treaty_2025.xlsx"
}

# Créer le gestionnaire de traités
treaty_manager = TreatyManager(treaty_paths)
```

### 2. Appliquer la logique claim_basis

```python
from structures.structure_engine import apply_treaty_manager_to_bordereau

# Calcul "as of now" en mi-2025
calculation_date = "2025-06-15"
results = apply_treaty_manager_to_bordereau(
    bordereau_df, treaty_manager, calculation_date
)
```

### 3. Analyser les résultats

```python
# Voir quel traité a été appliqué à chaque police
for _, result in results.iterrows():
    print(f"Police: {result['policy_number']}")
    print(f"Traité appliqué: {result['selected_treaty_year']}")
    print(f"Claim basis: {result['claim_basis']}")
    print(f"Statut: {result['coverage_status']}")
```

## Structure des fichiers Excel

### Feuille "structures"
Doit contenir les colonnes :
- `structure_name` : Nom de la structure
- `order` : Ordre d'application
- `product_type` : Type de produit (quote_share, excess_of_loss)
- `claim_basis` : **NOUVEAU** - "risk_attaching" ou "loss_occurring"
- `inception_date` : **NOUVEAU** - Date de début de la structure
- `expiry_date` : **NOUVEAU** - Date de fin de la structure

### Bordereau CSV
Doit contenir les colonnes :
- `inception_date` : **NOUVEAU** - Date de souscription de la police
- `expiry_date` : **NOUVEAU** - Date d'expiration de la police

## Exemples de résultats

### Police souscrite en 2023, calcul en 2025

| Claim Basis | Traité appliqué | Logique |
|-------------|-----------------|---------|
| `risk_attaching` | 2023 | Traité de l'année de souscription |
| `loss_occurring` | 2025 | Traité de l'année de calcul |

### Police sans traité correspondant

- **Résultat** : `coverage_status = "no_treaty_found"`
- **Cédé** : 0
- **Retenu** : Exposition totale

## Cas d'usage typiques

### 1. Évolution des conditions de traité
- **2023** : QS 25% + XOL 800K xs 400K
- **2024** : QS 30% + XOL 1M xs 500K  
- **2025** : QS 35% + XOL 1.2M xs 600K

### 2. Impact sur l'exposition
- **Risk Attaching** : Les polices gardent les conditions de leur année de souscription
- **Loss Occurring** : Toutes les polices utilisent les conditions actuelles

### 3. Gestion des polices anciennes
- Police 2022 avec `risk_attaching` → Aucune couverture (pas de traité 2022)
- Police 2022 avec `loss_occurring` → Couverture avec le traité actuel

## Fichiers d'exemple

- `treaty_2023.xlsx`, `treaty_2024.xlsx`, `treaty_2025.xlsx` : Traités multi-années
- `bordereau_multi_year_test.csv` : Bordereau de test
- `example_claim_basis_usage.py` : Exemple d'utilisation

## Tests

Exécuter les tests pour vérifier le bon fonctionnement :

```bash
uv run python example_claim_basis_usage.py
```

## Notes importantes

1. **Claim basis par structure** : Actuellement, toutes les structures d'un traité ont le même claim_basis
2. **Date de calcul** : Par défaut, utilise la date actuelle si non spécifiée
3. **Gestion des erreurs** : Le système gère gracieusement les cas où aucun traité n'est trouvé
4. **Performance** : Le système charge tous les traités en mémoire pour des performances optimales
