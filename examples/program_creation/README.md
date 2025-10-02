# Program Creation Scripts

Ce dossier contient les scripts Python pour créer les programmes de réassurance au format Excel.

## Principe

- **Maintenir les scripts** : Les scripts Python sont la source de vérité
- **Régénérer les Excel** : Les fichiers `.xlsx` sont générés à partir des scripts
- **Version control** : Seuls les scripts sont versionnés, pas les fichiers Excel

## Scripts disponibles

### Scripts de création
- `create_simple_programs.py` - Crée les programmes simples (QS + XOL)
- `create_aviation_old_republic.py` - Crée le programme aviation avec 3 couches XOL
- `create_program_config.py` - Crée un programme de base avec conditions géographiques

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
python create_simple_programs.py
python create_aviation_old_republic.py
python create_program_config.py
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

## Fichiers générés

Les programmes sont créés dans `examples/programs/` :
- `program_simple_sequential.xlsx`
- `program_simple_parallel.xlsx`
- `aviation_old_republic_2024.xlsx`
- `program_config.xlsx`
