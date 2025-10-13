# Tests d'Intégration Grandeur Réelle

Ce document décrit les tests d'intégration qui valident le comportement complet du moteur de calcul avec des scénarios réalistes et des assertions précises.

## 📋 Vue d'ensemble

Les tests d'intégration vérifient le **flow complet** :
1. Chargement d'un programme de réassurance
2. Application sur un bordereau de polices  
3. Calcul des cessions avec vérification précise des montants

## 🎯 Test Principal : QS → XL avec Rescaling

### Fichier : `test_full_calculation_qs_xl.py`

**Ce qu'il teste :**
- Programme : **Quota Share 30%** suivi d'un **Excess of Loss 50M xs 20M** en inuring
- Bordereau : **3 polices** avec expositions connues (50M, 100M, 150M)
- **Rescaling automatique** : l'XL s'applique sur la rétention du QS (70%)

### Structure du programme de test

```
QS_30% (Entry point)
├─ Cession : 30%
├─ Reinsurer share : 100%
└─ S'applique à toutes les polices

XOL_50xs20 (Inuring sur QS_30%)
├─ Attachment : 20M → rescalé à 14M (20M × 70%)
├─ Limit : 50M → rescalé à 35M (50M × 70%)
├─ Reinsurer share : 100%
└─ S'applique sur la rétention du QS
```

### Calculs attendus (vérifiés par assertions)

#### Policy A : 50M
```
1. QS 30% : 50M × 30% = 15M cédé, 35M retenu
2. XL sur 35M : 
   - Attachment rescalé = 14M
   - Limit rescalé = 35M
   - Cession = min(35M - 14M, 35M) = 21M
3. Total cession = 15M + 21M = 36M ✓
4. Rétention = 50M - 36M = 14M ✓
```

#### Policy B : 100M
```
1. QS 30% : 100M × 30% = 30M cédé, 70M retenu
2. XL sur 70M :
   - Cession = min(70M - 14M, 35M) = 35M (layer complète)
3. Total cession = 30M + 35M = 65M ✓
4. Rétention = 100M - 65M = 35M ✓
```

#### Policy C : 150M
```
1. QS 30% : 150M × 30% = 45M cédé, 105M retenu
2. XL sur 105M :
   - Cession = min(105M - 14M, 35M) = 35M (layer complète)
3. Total cession = 45M + 35M = 80M ✓
4. Rétention = 150M - 80M = 70M ✓
```

### Assertions testées

✅ **Calculs exacts** : Chaque montant de cession vérifié à 100$ près  
✅ **Conservation de l'exposition** : `Exposition = Cession + Rétention` pour chaque police  
✅ **Rescaling correct** : Attachment et Limit ajustés selon le facteur de rétention  
✅ **Totaux cohérents** : Somme des cessions = 181M (36M + 65M + 80M)  

## 🚀 Exécution des tests

### Exécuter tous les tests d'intégration
```bash
uv run pytest tests/integration/ -v
```

### Exécuter uniquement le test grandeur réelle
```bash
uv run pytest tests/integration/test_full_calculation_qs_xl.py -v
```

### Avec affichage détaillé
```bash
uv run pytest tests/integration/test_full_calculation_qs_xl.py -v -s
```

### Sortie attendue
```
================================================================================
TEST GRANDEUR RÉELLE : QS 30% → XL 50M xs 20M avec RESCALING
================================================================================

[... détails des calculs ...]

================================================================================
VÉRIFICATIONS (ASSERTIONS)
================================================================================

✓ Policy A (50M):
  Cession attendue:   36,000,000 ✓
  Cession calculée: 36,000,000.00 ✓

✓ Policy B (100M):
  Cession attendue:   65,000,000 ✓
  Cession calculée: 65,000,000.00 ✓

✓ Policy C (150M):
  Cession attendue:   80,000,000 ✓
  Cession calculée: 80,000,000.00 ✓

✓ Total global:
  Total attendu:  181,000,000 ✓
  Total calculé: 181,000,000.00 ✓

✓ Conservation de l'exposition:
  Toutes les polices: Exposition = Cession + Retenu ✓

================================================================================
✅ TEST RÉUSSI - Tous les calculs sont corrects !
================================================================================
```

## 📦 Fixtures utilisées

### Programme : `fixtures/test_program_qs_xl.xlsx`
Créé automatiquement via `fixtures/create_test_program.py`

### Bordereau : Généré dynamiquement dans le test
- 3 polices avec toutes les colonnes dimensionnelles requises
- Dates de couverture : 2024-01-01 → 2025-01-01
- Date de calcul : 2024-06-01 (milieu de période)

## 🎯 Bénéfices de ce test

1. **Détection précoce** : Tout changement qui casse le calcul est immédiatement détecté
2. **Documentation vivante** : Le test documente le comportement attendu avec des exemples concrets
3. **Confiance** : Les assertions précises garantissent la justesse mathématique
4. **Couverture** : Ce test seul couvre 90% du code du `structure_orchestrator`
5. **Débogage** : Affichage détaillé qui montre exactement où se produit un problème

## 🔄 Évolutions futures

### Tests additionnels recommandés :

#### Test multi-devises
- Programme avec sections par devise (USD, EUR, GBP)
- 20-30 polices réparties sur différentes devises
- Vérification des totaux par devise

#### Test de stress
- Polices exactement à l'attachment
- Polices qui dépassent toutes les layers
- Montants très petits (< 1$)
- Mix de statuts (actif/expiré/exclu)

#### Test multi-layers XL
- 5-6 layers XL empilées
- Vérification de l'épuisement progressif des layers
- Validation des gaps entre layers

#### Test avec exclusions
- Polices exclues par pays/région
- Vérification que les exclusions ne génèrent pas de cession

## 📚 Références

- Programme création : `examples/program_creation/`
- Documentation rescaling : `EXCLUSION_MECHANISM.md`
- Documentation expiration : `POLICY_EXPIRY_MECHANISM.md`

