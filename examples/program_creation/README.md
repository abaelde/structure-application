# Program Creation Scripts

Ce dossier contient les scripts Python pour créer les programmes de réassurance au format Excel.

## Principe

- **Maintenir les scripts** : Les scripts Python sont la source de vérité
- **Régénérer les Excel** : Les fichiers `.xlsx` sont générés à partir des scripts
- **Version control** : Seuls les scripts sont versionnés, pas les fichiers Excel

## Scripts disponibles

### Scripts de création
- `create_single_quota_share.py` - Crée un programme simple avec quota share (30%)
- `create_single_excess_of_loss.py` - Crée un programme simple avec excess of loss (1M xs 0.5M)
- `create_aviation_old_republic.py` - Crée le programme aviation avec 3 couches XOL empilées
- `create_aviation_AXA_XL.py` - Crée un programme aviation complexe avec 6 couches XOL multi-devises

### Script maître
- `regenerate_all_programs.py` - Régénère tous les programmes d'un coup

## Utilisation

### Régénérer tous les programmes
```bash
cd examples/program_creation
python regenerate_all_programs.py
```

### Créer un programme spécifique
```bash
cd examples/program_creation
python create_single_quota_share.py
python create_single_excess_of_loss.py
python create_aviation_old_republic.py
python create_aviation_AXA_XL.py
```

## Structure des programmes créés

Tous les programmes suivent la nouvelle logique **ordre-based** :
- **Structures** : Appliquées séquentiellement selon leur ordre
- **Sections** : Appliquées en parallèle selon les conditions de matching
- **Quote Share** : Réduit l'exposition restante
- **Excess of Loss** : S'applique sur l'exposition restante (empilés)

## Valeurs en millions

Tous les montants sont exprimés en millions pour la lisibilité :
- Priorité 0.5 = 500,000
- Limite 1.0 = 1,000,000
- Exposition 2.0 = 2,000,000

## Claim Basis

Tous les programmes incluent maintenant le champ `claim_basis` dans la feuille "structures" :
- **`risk_attaching`** : Le traité s'applique selon l'année de souscription de la police
- **`loss_occurring`** : Le traité s'applique selon l'année de survenance du sinistre

Pour les programmes actuels, tous les structures utilisent `risk_attaching`.

## Reinsurer Share

Tous les programmes incluent maintenant le champ `reinsurer_share` dans la feuille "sections" :
- **Configuration** : Défini dans le dictionnaire `REINSURER_SHARE_VALUES` pour chaque structure
- **Utilisation** : Permet de définir le pourcentage de la part cédée qui est effectivement réassurée
- **Exemple** : Si `reinsurer_share = 0.8`, alors 80% de la part cédée est réassurée, 20% reste en rétention
- **Modification** : Éditez le dictionnaire `REINSURER_SHARE_VALUES` dans le script Python

Cette colonne est positionnée après `limit` dans la structure des sections.

### Exemple de configuration :
```python
REINSURER_SHARE_VALUES = {
    "XOL_1": 1.0,   # 100% réassuré
    "XOL_2": 0.8,   # 80% réassuré, 20% en rétention
    "XOL_3": 1.0,   # 100% réassuré
}
```

## Fichiers générés

Les programmes sont créés dans `examples/programs/` :
- `single_quota_share.xlsx` - Programme simple avec quota share 30%
- `single_excess_of_loss.xlsx` - Programme simple avec XOL 1M xs 0.5M
- `aviation_old_republic_2024.xlsx` - Programme aviation avec 3 couches XOL empilées
- `aviation_axa_xl_2024.xlsx` - Programme aviation complexe avec 6 couches XOL multi-devises
