# Mécanisme d'Exclusion

## Vue d'ensemble

Le système de réassurance supporte maintenant un mécanisme d'exclusion permettant d'exclure certaines polices de l'application d'un programme de réassurance.

## Fonctionnement

### Principe

Lorsqu'une police matche une section d'exclusion :
- **L'exposition effective devient 0**
- Aucune cession n'est calculée
- La police est marquée comme "excluded" dans les résultats

### Ordre de traitement

Pour chaque police du bordereau, le système vérifie **dans cet ordre** :

1. **Exclusions** : La police matche-t-elle une section d'exclusion ?
   - Si OUI → exposition = 0, arrêt du traitement
   - Si NON → continuer

2. **Cas particuliers** : Sections avec conditions spécifiques (haute spécificité)

3. **Cas général** : Section par défaut (peu ou pas de conditions)

## Configuration dans le programme Excel

### Colonne `BUSCL_EXCLUDE_CD`

Dans la feuille `sections` du programme Excel :

- **Vide** (ou NULL) : Section normale (inclusion)
- **`"exclude"`** : Section d'exclusion

### Exemple de configuration

```
INSPER_ID_PRE | BUSCL_EXCLUDE_CD | BUSCL_COUNTRY_CD | CESSION_PCT | ...
--------------|------------------|------------------|-------------|----
1             | exclude          | Iran             | NULL        | ...
1             | exclude          | Russia           | NULL        | ...
1             | exclude          | NULL             | NULL        | ... (BUSCL_REGION=Sanctioned)
1             | NULL             | NULL             | 0.25        | ... (section normale)
```

Dans cet exemple :
- Les polices d'Iran sont exclues
- Les polices de Russie sont exclues
- Les polices de la région "Sanctioned" sont exclues
- Toutes les autres polices ont 25% de cession

## Résultats

### Nouveaux champs dans les résultats

Chaque résultat contient maintenant :

- **`exposure`** : Exposition originale de la police
- **`effective_exposure`** : Exposition effective après application des exclusions
  - = `exposure` si inclus
  - = `0` si exclu
- **`exclusion_status`** : Statut de la police
  - `"included"` : Police incluse dans le programme
  - `"excluded"` : Police exclue du programme
- **`exclusion_reason`** : Raison de l'exclusion (si applicable)

### Exemple de résultat

```python
{
    "INSURED_NAME": "IRAN AIR",
    "exposure": 30.0,
    "effective_exposure": 0.0,
    "cession_to_layer_100pct": 0.0,
    "cession_to_reinsurer": 0.0,
    "retained_by_cedant": 0.0,
    "exclusion_status": "excluded",
    "exclusion_reason": "Matched exclusion rule",
    ...
}
```

## Test

Un exemple complet est disponible dans :
- **Programme** : `examples/programs/quota_share_with_exclusion.xlsx`
- **Bordereau** : `examples/bordereaux/aviation/bordereau_exclusion_test.csv`
- **Script de test** : `test_exclusion_mechanism.py`

### Exécuter le test

```bash
uv run python test_exclusion_mechanism.py
```

### Résultats attendus

Le test doit montrer :
- 3 polices exclues (Iran Air, Aeroflot, Sanctioned Airline)
- 4 polices incluses avec cession de 25%
- Exposition effective = 0 pour les polices exclues

## Cas d'usage

### Sanctions économiques

Exclure les pays sous sanctions :

```
BUSCL_EXCLUDE_CD | BUSCL_COUNTRY_CD
exclude          | Iran
exclude          | Russia
exclude          | North Korea
```

### Régions à risque

Exclure certaines régions :

```
BUSCL_EXCLUDE_CD | BUSCL_REGION
exclude          | War Zone
exclude          | Sanctioned
```

### Classes de business spécifiques

Exclure certaines classes de business :

```
BUSCL_EXCLUDE_CD | BUSCL_CLASS_OF_BUSINESS_1
exclude          | Nuclear
exclude          | Terrorism
```

### Combinaisons

Les exclusions peuvent combiner plusieurs dimensions :

```
BUSCL_EXCLUDE_CD | BUSCL_COUNTRY_CD | BUSCL_CLASS_OF_BUSINESS_1
exclude          | Russia           | Military
exclude          | Iran             | Aviation
```

## Implémentation technique

### Fonctions principales

#### `check_exclusion()`
Vérifie si une police matche une section d'exclusion.

#### `match_section()`
Modifiée pour ignorer les sections d'exclusion lors du matching normal.

#### `apply_program()`
Modifiée pour vérifier les exclusions **en premier** avant d'appliquer le programme.

### Fichiers modifiés

- `src/engine/calculation_engine.py` : Ajout de la logique d'exclusion

## Notes importantes

1. **Priorité** : Les exclusions sont toujours vérifiées en premier, avant tout autre traitement

2. **Matching** : Les sections d'exclusion utilisent le même mécanisme de matching par spécificité que les sections normales

3. **Exposition** : L'exposition originale est conservée pour tracking, mais l'exposition effective est mise à 0

4. **Rétrocompatibilité** : Les programmes sans exclusions fonctionnent normalement (tous les champs `BUSCL_EXCLUDE_CD` sont vides)

## Migration

Pour les programmes existants :
- Aucune migration nécessaire
- Ajouter simplement des lignes avec `BUSCL_EXCLUDE_CD = "exclude"` dans la feuille `sections` pour activer les exclusions

