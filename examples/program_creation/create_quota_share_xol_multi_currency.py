"""
Création d'un programme avec Quota Share + Excess of Loss Multi-Devises + Exclusion

Programme: Quota Share + XOL Multi-Currency with Exclusion
- 1 structure Quota Share de 30% par défaut
- 1 structure Excess of Loss avec conditions spécifiques par devise:
  * EUR: 10M xs 5M
  * GBP: 8M xs 4M  
  * USD: 12M xs 6M
- 1 exclusion globale: pays à risque (Iran, Russia, North Korea)
"""

# =============================================================================
# CONFIGURATION
# =============================================================================
# Ce script utilise Snowpark pour la sauvegarde des programmes
# La configuration Snowflake est chargée depuis le fichier snowflake_config.env

# =============================================================================
# SCRIPT
# =============================================================================

import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.builders import build_quota_share, build_excess_of_loss, build_program
from src.domain.exclusion import ExclusionRule
from snowflake_utils.utils_snowpark import save_program_snowpark

print("Création du programme Quota Share + XOL Multi-Currency with Exclusion...")
print("Backend de sauvegarde: Snowpark")

# =============================================================================
# CONFIGURATION DES STRUCTURES
# =============================================================================

# Configuration du Quota Share
QS_CESSION_RATE = 0.30  # 30% cédé
QS_REINSURER_SHARE = 0.15  # 15% signed share

# Configuration de l'Excess of Loss par devise
XOL_CONDITIONS = {
    "EUR": {
        "attachment": 5_000_000,
        "limit": 10_000_000,
        "signed_share": 0.10,  # 10%
    },
    "GBP": {
        "attachment": 4_000_000,
        "limit": 8_000_000,
        "signed_share": 0.10,  # 10%
    },
    "USD": {
        "attachment": 6_000_000,
        "limit": 12_000_000,
        "signed_share": 0.10,  # 10%
    },
}

# =============================================================================
# CONSTRUCTION DU QUOTA SHARE
# =============================================================================

qs = build_quota_share(
    name="QS_30_Multi_Currency",
    cession_pct=QS_CESSION_RATE,
    signed_share=QS_REINSURER_SHARE,
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2025-01-01",
)

print(f"✓ Quota Share créé: {QS_CESSION_RATE:.0%} cédé, {QS_REINSURER_SHARE:.0%} signed share")

# =============================================================================
# CONSTRUCTION DE L'EXCESS OF LOSS MULTI-DEVISES
# =============================================================================

# Créer les conditions spéciales pour chaque devise
xol_special_conditions = []

for currency, config in XOL_CONDITIONS.items():
    condition = {
        "CURRENCY": [currency],  # Utiliser le paramètre CURRENCY du builder
        "attachment": config["attachment"],
        "limit": config["limit"],
        "signed_share": config["signed_share"],
    }
    xol_special_conditions.append(condition)
    print(f"✓ Condition {currency}: {config['limit']:,}M xs {config['attachment']:,}M ({config['signed_share']:.0%} signed share)")

# Construire l'Excess of Loss
xol = build_excess_of_loss(
    name="XOL_Multi_Currency",
    # Valeurs par défaut (ne s'appliqueront pas car toutes les conditions sont spécifiques)
    attachment=5_000_000,
    limit=10_000_000,
    signed_share=0.10,
    special_conditions=xol_special_conditions,
    predecessor_title="QS_30_Multi_Currency",  # L'XOL s'applique après le QS
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2025-01-01",
)

print(f"✓ Excess of Loss créé avec {len(xol_special_conditions)} conditions par devise")

# =============================================================================
# CONSTRUCTION DES EXCLUSIONS
# =============================================================================

exclusions = [
    ExclusionRule(
        name="High_Risk_Countries",
        values_by_dimension={
            "COUNTRIES": ["Iran", "Russia", "North Korea"],
        },
        effective_date="2024-01-01",
        expiry_date="2025-01-01",
    ),
]

print(f"✓ Exclusion créée: {len(exclusions[0].values_by_dimension['COUNTRIES'])} pays à risque")

# =============================================================================
# CONSTRUCTION DU PROGRAMME
# =============================================================================

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
program_name = f"QUOTA_SHARE_XOL_MULTI_CURRENCY_{timestamp}"

program = build_program(
    name=program_name,
    structures=[qs, xol],
    main_currency="EUR",
    underwriting_department="casualty",
    exclusions=exclusions,
    # Spécifier explicitement les dimensions utilisées dans les conditions
    dimension_columns=["COUNTRY", "CURRENCY", "PRODUCT_TYPE_LEVEL_1", "PRODUCT_TYPE_LEVEL_2", "PRODUCT_TYPE_LEVEL_3", "REGION"],
)

# Sauvegarde avec l'utilitaire Snowpark
try:
    success = save_program_snowpark(program, program_name)
    if success:
        print(f"✓ Programme sauvegardé avec succès via Snowpark: {program_name}")
    else:
        print(f"❌ Échec de la sauvegarde du programme: {program_name}")
except Exception as e:
    print(f"❌ Erreur lors de la sauvegarde: {e}")
    print("Le programme a été construit correctement mais la sauvegarde a échoué.")

# =============================================================================
# AFFICHAGE
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME QUOTA SHARE + XOL MULTI-CURRENCY WITH EXCLUSION")
print("=" * 80)

program.describe()

print("\n" + "=" * 80)
print("RÉSUMÉ DU PROGRAMME")
print("=" * 80)

print(f"""
Programme: {program_name}
Type: Casualty - Quota Share + Excess of Loss Multi-Devises avec Exclusion
Devise principale: EUR
Département: casualty

STRUCTURES:

1. QS_30_Multi_Currency (Quota Share):
   - Cession: {QS_CESSION_RATE:.0%} par défaut
   - Signed share: {QS_REINSURER_SHARE:.0%}
   - S'applique à toutes les polices
   - Retient {1-QS_CESSION_RATE:.0%} (qui devient l'input de l'XOL)

2. XOL_Multi_Currency (Excess of Loss):
   - S'applique après le Quota Share (inuring)
   - Conditions spécifiques par devise:
     * EUR: {XOL_CONDITIONS['EUR']['limit']:,}M xs {XOL_CONDITIONS['EUR']['attachment']:,}M ({XOL_CONDITIONS['EUR']['signed_share']:.0%} signed share)
     * GBP: {XOL_CONDITIONS['GBP']['limit']:,}M xs {XOL_CONDITIONS['GBP']['attachment']:,}M ({XOL_CONDITIONS['GBP']['signed_share']:.0%} signed share)
     * USD: {XOL_CONDITIONS['USD']['limit']:,}M xs {XOL_CONDITIONS['USD']['attachment']:,}M ({XOL_CONDITIONS['USD']['signed_share']:.0%} signed share)

EXCLUSIONS:

1. High_Risk_Countries:
   - Pays exclus: {', '.join(exclusions[0].values_by_dimension['COUNTRIES'])}
   - Période: 2024-01-01 à 2025-01-01
   - S'applique à toutes les structures

FONCTIONNEMENT:

1. Les polices arrivent dans le programme
2. L'exclusion filtre les pays à risque (Iran, Russia, North Korea)
3. Le Quota Share cède {QS_CESSION_RATE:.0%} et retient {1-QS_CESSION_RATE:.0%}
4. L'Excess of Loss s'applique sur la partie retenue selon la devise:
   - EUR: couvre de 5M à 15M
   - GBP: couvre de 4M à 12M  
   - USD: couvre de 6M à 18M
""")

print("✓ Le programme Quota Share + XOL Multi-Currency with Exclusion est prêt !")
