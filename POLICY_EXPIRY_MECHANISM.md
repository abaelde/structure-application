# Mécanisme de Vérification d'Activité des Polices

## Vue d'ensemble

Le système de calcul des cessions vérifie automatiquement si les polices sous-jacentes du bordereau sont encore actives à la date de calcul. Une police est considérée comme **inactive** si sa date d'expiration est antérieure ou égale à la date de calcul.

## Principe de fonctionnement

### Logique de vérification

Pour chaque police dans le bordereau :

```
Si EXPIRE_DT <= calculation_date :
    ➜ Police INACTIVE
    ➜ effective_exposure = 0
    ➜ cession_to_reinsurer = 0
    ➜ exclusion_status = "inactive"

Sinon :
    ➜ Police ACTIVE
    ➜ Calcul normal des cessions
```

### Date de calcul

- Par défaut : date du jour (`datetime.now()`)
- Peut être spécifiée explicitement via le paramètre `calculation_date` (format : `YYYY-MM-DD`)

## Implémentation

### Fonctions concernées

1. **`apply_program(policy_data, program, calculation_date=None)`**
   - Vérifie l'activité de la police avant tout calcul
   - Retourne immédiatement si la police est expirée
   - Passe la `calculation_date` en paramètre

2. **`apply_program_to_bordereau(bordereau_df, program, calculation_date=None)`**
   - Propage la `calculation_date` à chaque police du bordereau

### Code de vérification

```python
policy_expiry_date = policy_data.get(FIELDS["EXPIRY_DATE"])

if calculation_date is None:
    calculation_date = datetime.now().strftime("%Y-%m-%d")

is_policy_active = True
inactive_reason = None

if policy_expiry_date:
    try:
        expiry_dt = pd.to_datetime(policy_expiry_date)
        calc_dt = pd.to_datetime(calculation_date)
        
        if expiry_dt <= calc_dt:
            is_policy_active = False
            inactive_reason = f"Policy expired on {expiry_dt.date()} (calculation date: {calc_dt.date()})"
    except Exception:
        pass

if not is_policy_active:
    return {
        FIELDS["INSURED_NAME"]: policy_data.get(FIELDS["INSURED_NAME"]),
        "exposure": exposure,
        "effective_exposure": 0.0,
        "cession_to_layer_100pct": 0.0,
        "cession_to_reinsurer": 0.0,
        "retained_by_cedant": 0.0,
        "policy_inception_date": policy_data.get(FIELDS["INCEPTION_DATE"]),
        "policy_expiry_date": policy_expiry_date,
        "structures_detail": [],
        "exclusion_status": "inactive",
        "exclusion_reason": inactive_reason,
    }
```

## Statuts d'exclusion

Le champ `exclusion_status` peut avoir les valeurs suivantes :

| Status | Description |
|--------|-------------|
| `included` | Police active et non exclue, calcul normal |
| `excluded` | Police exclue par une règle d'exclusion |
| `inactive` | Police expirée à la date de calcul |

## Résultats pour une police inactive

Lorsqu'une police est inactive :

```python
{
    "INSURED_NAME": "COMPANY A",
    "exposure": 1000000,              # Exposition originale conservée
    "effective_exposure": 0.0,        # Exposition effective = 0
    "cession_to_layer_100pct": 0.0,   # Pas de cession
    "cession_to_reinsurer": 0.0,      # Pas de cession au réassureur
    "retained_by_cedant": 0.0,        # Rien retenu (car exposition = 0)
    "policy_inception_date": "2024-01-01",
    "policy_expiry_date": "2025-01-01",
    "structures_detail": [],          # Aucune structure appliquée
    "exclusion_status": "inactive",
    "exclusion_reason": "Policy expired on 2025-01-01 (calculation date: 2025-07-01)"
}
```

## Exemples d'utilisation

### Exemple 1 : Date de calcul par défaut (date du jour)

```python
from src.loaders import ProgramLoader, BordereauLoader
from src.engine.calculation_engine import apply_program_to_bordereau

loader = ProgramLoader("program.xlsx")
program = loader.get_program()

bordereau_df = pd.read_csv("bordereau.csv")

# Utilise la date du jour comme date de calcul
_, results_df = apply_program_to_bordereau(bordereau_df, program)
```

### Exemple 2 : Date de calcul spécifique

```python
# Calcul "as of" au 31/12/2024
_, results_df = apply_program_to_bordereau(
    bordereau_df, 
    program, 
    calculation_date="2024-12-31"
)
```

## Test

Un test complet est disponible dans `test_policy_expiry.py` :

```bash
uv run python test_policy_expiry.py
```

Ce test démontre :
- Le comportement avec différentes dates de calcul
- Le passage de polices actives à inactives selon la date
- L'impact sur les cessions totales

## Impact sur les rapports

Les polices inactives sont :
- Incluses dans les résultats avec `exclusion_status = "inactive"`
- Comptabilisées avec `effective_exposure = 0`
- Exclues du calcul des cessions
- Documentées avec une raison d'inactivité explicite

Cela permet de :
1. **Tracer** toutes les polices du bordereau (même expirées)
2. **Comprendre** pourquoi certaines polices n'ont pas de cession
3. **Auditer** les calculs avec transparence
4. **Calculer** l'exposition active à une date donnée

## Comparaison avec le mécanisme d'exclusion

| Critère | Exclusion | Inactivité |
|---------|-----------|------------|
| Déclenchement | Règle d'exclusion dans le programme | Date d'expiration ≤ date de calcul |
| `exclusion_status` | `"excluded"` | `"inactive"` |
| `effective_exposure` | 0 | 0 |
| `exclusion_reason` | "Matched exclusion rule" | "Policy expired on..." |
| Configuration | Section avec `BUSCL_EXCLUDE_CD = "exclude"` | Automatique |

## Notes importantes

1. **Comparaison stricte** : `expiry_dt <= calc_dt` (une police qui expire le jour du calcul est considérée comme inactive)
2. **Exposition originale conservée** : Le champ `exposure` conserve la valeur originale pour traçabilité
3. **Gestion des erreurs** : Si la date d'expiration est invalide, la police est traitée comme active
4. **Compatibilité** : Fonctionne avec tous les types de programmes (quota share, excess of loss, multi-traités)

