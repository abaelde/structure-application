# Program Creation - Data Model Constraints

Ce document définit les contraintes du modèle de données pour la création de programmes de réassurance.

## Structure des Fichiers Excel

Chaque programme doit être un fichier Excel avec **3 feuilles obligatoires** :

### 1. Feuille "program" (1 ligne)
**Contraintes :**
- **REPROG_ID_PRE** : INTEGER, clé primaire auto-incrémentée (commence à 1)
- **REPROG_TITLE** : VARCHAR(255), nom du programme (obligatoire)
- **CED_ID_PRE** : INTEGER, ID du cédant (peut être NULL)
- **CED_NAME_PRE** : VARCHAR(255), nom du cédant (peut être NULL)
- **REPROG_ACTIVE_IND** : BOOLEAN, indicateur d'activation (défaut: TRUE)
- **REPROG_COMMENT** : VARCHAR, commentaires (peut être NULL)
- **REPROG_UW_DEPARTMENT_CD** : VARCHAR(255), code département UW (peut être NULL)
- **REPROG_UW_DEPARTMENT_NAME** : VARCHAR(255), nom département UW (peut être NULL)
- **REPROG_UW_DEPARTMENT_LOB_CD** : VARCHAR(255), code LOB département (peut être NULL)
- **REPROG_UW_DEPARTMENT_LOB_NAME** : VARCHAR(255), nom LOB département (peut être NULL)
- **BUSPAR_CED_REG_CLASS_CD** : VARCHAR(255), code classe réglementaire (peut être NULL)
- **BUSPAR_CED_REG_CLASS_NAME** : VARCHAR(255), nom classe réglementaire (peut être NULL)
- **REPROG_MAIN_CURRENCY_CD** : VARCHAR(255), code devise principale (peut être NULL)
- **REPROG_MANAGEMENT_REPORTING_LOB_CD** : VARCHAR(255), code LOB reporting (peut être NULL)

### 2. Feuille "structures" (n lignes)
**Contraintes :**
- **structure_name** : VARCHAR(255), nom unique de la structure (obligatoire)
- **contract_order** : INTEGER, ordre d'application séquentiel (commence à 0)
- **type_of_participation** : ENUM('quota_share', 'excess_of_loss'), type de produit (obligatoire)
- **claim_basis** : ENUM('risk_attaching', 'loss_occurring'), base de sinistre (peut être NULL)
- **inception_date** : DATE, date de début (peut être NULL)
- **expiry_date** : DATE, date de fin (peut être NULL)

### 3. Feuille "sections" (n lignes)
**Contraintes :**
- **structure_name** : VARCHAR(255), référence vers structures.structure_name (obligatoire)
- **cession_PCT** : DECIMAL(0-1), pourcentage de cession pour quota_share (peut être NULL pour XOL)
- **attachment_point_100** : DECIMAL, priorité pour excess_of_loss en millions (peut être NULL pour QS)
- **limit_occurrence_100** : DECIMAL, limite pour excess_of_loss en millions (peut être NULL pour QS)
- **reinsurer_share** : DECIMAL(0-1), part du réassureur dans la cession (peut être NULL)
- **country** : VARCHAR(255), condition géographique (peut être NULL = pas de condition)
- **region** : VARCHAR(255), condition régionale (peut être NULL = pas de condition)
- **product_type_1** : VARCHAR(255), condition type produit niveau 1 (peut être NULL = pas de condition)
- **product_type_2** : VARCHAR(255), condition type produit niveau 2 (peut être NULL = pas de condition)
- **product_type_3** : VARCHAR(255), condition type produit niveau 3 (peut être NULL = pas de condition)
- **currency** : VARCHAR(255), condition devise (peut être NULL = pas de condition)
- **line_of_business** : VARCHAR(255), condition ligne de business (peut être NULL = pas de condition)
- **industry** : VARCHAR(255), condition industrie (peut être NULL = pas de condition)
- **sic_code** : VARCHAR(255), condition code SIC (peut être NULL = pas de condition)
- **include** : VARCHAR(255), condition libre (peut être NULL = pas de condition)

## Contraintes de Cohérence

### Contraintes Structurelles
1. **contract_order** : Doit être unique et séquentiel (0, 1, 2, ...)
2. **structure_name** : Doit être unique dans la feuille structures
3. **structure_name** dans sections : Doit référencer une structure existante

### Contraintes Logiques
1. **quota_share** : 
   - `cession_PCT` obligatoire (0-1)
   - `attachment_point_100` et `limit_occurrence_100` doivent être NULL
2. **excess_of_loss** :
   - `attachment_point_100` et `limit_occurrence_100` obligatoires (≥ 0)
   - `cession_PCT` doit être NULL

### Contraintes de Valeurs
1. **Montants** : Tous les montants sont exprimés en millions
2. **Pourcentages** : Tous les pourcentages sont exprimés en décimal (0.25 = 25%)
3. **Dates** : Format ISO (YYYY-MM-DD) ou NULL

## Rétrocompatibilité

Le système supporte l'ancien format avec `program_name` au lieu de `REPROG_TITLE` pour assurer la compatibilité avec les programmes existants.

## Scripts de Création

Utilisez les scripts Python existants comme modèles :
- `create_single_quota_share.py` - Exemple simple
- `create_aviation_AXA_XL.py` - Exemple complexe multi-devises
- `regenerate_all_programs.py` - Régénération en lot

## Validation

Avant de créer un nouveau programme, vérifiez :
1. Toutes les contraintes structurelles sont respectées
2. Les types de participation correspondent aux paramètres
3. Les références entre feuilles sont cohérentes
4. Les valeurs numériques sont dans les bonnes unités (millions)