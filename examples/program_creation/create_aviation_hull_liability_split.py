"""
Création d'un programme Aviation avec séparation Hull/Liability

Ce programme démontre le nouveau mécanisme de filtrage Hull/Liability
qui permet de créer des structures s'appliquant sélectivement sur une
partie de l'exposition aviation.

Programme:
- QS_ALL: Quota Share 25% sur Hull + Liability (défaut)
- XOL_HULL: Excess of Loss sur Hull uniquement
- XOL_LIABILITY: Excess of Loss sur Liability uniquement
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.builders import build_quota_share, build_excess_of_loss, build_program
from src.managers import ProgramManager

print("Création du programme Aviation avec filtrage Hull/Liability...")

qs_all = build_quota_share(
    name="QS_ALL",
    conditions_config=[
        {
            "cession_pct": 0.25,
            "limit": 575_000_000,
            "signed_share": 0.0165,
            "includes_hull": True,
            "includes_liability": True,
        }
    ],
    claim_basis="risk_attaching",
)

xol_hull = build_excess_of_loss(
    name="XOL_HULL",
    conditions_config=[
        {
            "attachment": 5_000_000,
            "limit": 10_000_000,
            "signed_share": 0.05,
            "includes_hull": True,
            "includes_liability": False,
        }
    ],
    predecessor_title="QS_ALL",
    claim_basis="risk_attaching",
)

xol_liability = build_excess_of_loss(
    name="XOL_LIABILITY",
    conditions_config=[
        {
            "attachment": 10_000_000,
            "limit": 40_000_000,
            "signed_share": 0.05,
            "includes_hull": False,
            "includes_liability": True,
        }
    ],
    predecessor_title="QS_ALL",
    claim_basis="risk_attaching",
)

program = build_program(
    name="AVIATION_HULL_LIABILITY_SPLIT",
    structures=[qs_all, xol_hull, xol_liability],
    underwriting_department="aviation",
)

output_dir = "../programs"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "aviation_hull_liability_split.xlsx")

manager = ProgramManager(backend="excel")
manager.save(program, output_file)

print(f"✓ Programme créé: {output_file}")

print("\n" + "=" * 80)
print("PROGRAMME AVIATION HULL/LIABILITY SPLIT")
print("=" * 80)

program.describe()

print("\n" + "=" * 80)
print("RÉSUMÉ DU MÉCANISME")
print("=" * 80)

print(
    """
Ce programme illustre le nouveau mécanisme de filtrage Hull/Liability :

1. QS_ALL (Structure par défaut):
   - S'applique sur l'exposition totale (Hull + Liability)
   - Cède 25% au réassureur
   - Retient 75% (qui devient l'input des structures suivantes)

2. XOL_HULL (Structure Hull-only):
   - Colonne INCLUDES_HULL = TRUE
   - Colonne INCLUDES_LIABILITY = FALSE
   - Ne s'applique QUE sur la composante Hull de l'exposition retenue
   - Exemple : Si Hull = 15M et Liability = 50M, après QS:
     * Retained total = 48.75M
     * Composante Hull = 11.25M
     * XOL_HULL voit uniquement 11.25M

3. XOL_LIABILITY (Structure Liability-only):
   - Colonne INCLUDES_HULL = FALSE
   - Colonne INCLUDES_LIABILITY = TRUE
   - Ne s'applique QUE sur la composante Liability
   - Avec le même exemple:
     * Composante Liability = 37.5M
     * XOL_LIABILITY voit uniquement 37.5M

UTILISATION:

Dans Excel, ajoutez simplement deux colonnes optionnelles dans la feuille "conditions":
- INCLUDES_HULL (TRUE/FALSE, défaut: TRUE)
- INCLUDES_LIABILITY (TRUE/FALSE, défaut: TRUE)

Si ces colonnes sont absentes, le comportement par défaut est de tout inclure
(compatibilité ascendante avec les programmes existants).

ATTENTION:

Ce mécanisme est UNIQUEMENT pour Aviation. Pour Casualty, ces colonnes
sont ignorées car il n'y a qu'une seule notion d'exposition.
"""
)

print("✓ Le programme Aviation Hull/Liability Split est prêt !")
