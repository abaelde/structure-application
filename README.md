# Reinsurance Program Application System

Système d'application de programmes de réassurance sur des bordereaux.

## Architecture

### Structure du projet

```
structure-application/
├── products/                      # Building blocks de réassurance
│   ├── base_products.py          # quote_share & excess_of_loss
│   └── __init__.py
├── structures/                    # Moteur d'application des programmes
│   ├── structure_loader.py       # Chargement depuis Excel (ProgramLoader)
│   ├── structure_engine.py       # Logique d'application (sequential/parallel)
│   └── __init__.py
├── bordereau_exemple.csv         # Données des polices
├── program_config.xlsx           # Configuration du programme (Excel)
├── main.py                       # Point d'entrée principal
└── README.md                     # Documentation
```

## Concepts

### 1. Bordereau
Fichier CSV contenant les polices d'assurance avec :
- `numero_police` : Identifiant unique
- `nom_assure` : Nom de l'assuré
- `localisation` : Localisation géographique
- `industrie` : Secteur d'activité
- `exposition` : Valeur d'exposition

### 2. Produits de base
- **Quote-share** : Application d'un pourcentage de cession (session_rate) sur l'exposition
- **Excess of Loss (XoL)** : Couverture au-dessus d'une priorité (priority) jusqu'à une limite (limit)

### 3. Program
Un fichier de configuration contient **un seul programme** qui est constitué de **plusieurs structures**.

Le programme définit :
- **Nom** : Identifiant du programme
- **Mode** : Comment les structures s'appliquent
  - `sequential` : Les structures s'appliquent successivement (la sortie de l'une devient l'entrée de la suivante)
  - `parallel` : Chaque structure s'applique indépendamment sur l'exposition initiale

### 4. Structures
Les structures sont les éléments qui composent un programme. Chaque structure :
- Utilise un produit de base (quote_share ou excess_of_loss)
- A des paramètres spécifiques (session_rate, priority, limit)
- Peut avoir des conditions d'application

### 5. Conditions d'application
Les structures peuvent avoir des conditions basées sur les métadonnées du bordereau :
- **dimension** : Le champ du bordereau à vérifier (ex: localisation, industrie)
- **value** : La valeur exacte requise (opérateur = equals uniquement)

**Important** : Si une structure doit s'appliquer à plusieurs valeurs (ex: Paris ET Lyon), 
on crée **plusieurs lignes de conditions** avec une valeur unique par ligne.

## Configuration Excel

Le fichier `program_config.xlsx` contient 3 feuilles :

### Feuille "program"
Définit le programme principal (une seule ligne).

| program_name | mode       |
|--------------|------------|
| PROGRAM_2024 | sequential |

### Feuille "structures"
Définit les structures du programme.

| structure_name | order | product_type    | session_rate | priority | limit   |
|----------------|-------|-----------------|--------------|----------|---------|
| QS_30_PARIS    | 1     | quote_share     | 0.30         | -        | -       |
| XOL_1M_xs_500K | 2     | excess_of_loss  | -            | 500000   | 1000000 |
| QS_20_TECH     | 3     | quote_share     | 0.20         | -        | -       |

### Feuille "conditions"
Définit les conditions pour chaque structure (une valeur par ligne).

| structure_name | dimension    | value       |
|----------------|--------------|-------------|
| QS_30_PARIS    | localisation | Paris       |
| XOL_1M_xs_500K | localisation | Paris       |
| QS_20_TECH     | localisation | Lyon        |
| QS_20_TECH     | industrie    | Technologie |

**Note** : Pour QS_20_TECH, il y a 2 lignes de conditions car la structure nécessite 
`localisation=Lyon` **ET** `industrie=Technologie`.

## Utilisation

```bash
# Installer les dépendances
uv sync

# Exécuter le système
uv run python main.py
```

## Exemple de résultat

**PROGRAM_2024 (sequential)** avec 3 structures :

### Police POL-2024-001 (Paris, Construction, 500K€)
1. **QS_30_PARIS** ✓ Appliquée : 500K€ × 30% = 150K€ cédés
2. **XOL_1M_xs_500K** ✓ Appliquée : sur 350K€ restants → 0€ cédé (sous la priorité)
3. **QS_20_TECH** ✗ Non appliquée : condition industrie=Technologie non remplie

**Total cédé : 150K€**

### Police POL-2024-002 (Lyon, Technologie, 750K€)
1. **QS_30_PARIS** ✗ Non appliquée : condition localisation=Paris non remplie
2. **XOL_1M_xs_500K** ✗ Non appliquée : condition localisation=Paris non remplie
3. **QS_20_TECH** ✓ Appliquée : 750K€ × 20% = 150K€ cédés

**Total cédé : 150K€**

## Nomenclature

- **Program** : Le programme global (un par fichier)
- **Structure** : Un élément du programme utilisant un produit de base
- **Product** : Les building blocks (quote_share, excess_of_loss)
- **Dimension** : Le champ du bordereau utilisé dans une condition
- **Session rate** : Le taux de cession pour une quote-share
