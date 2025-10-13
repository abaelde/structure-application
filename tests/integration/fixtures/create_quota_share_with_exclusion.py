import sys
from pathlib import Path

# Navigate to project root (same logic as conftest.py but 2 levels deeper)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

output_file = Path(__file__).parent / "programs" / "quota_share_with_exclusion.xlsx"

program_df = pd.DataFrame(
    [
        {
            "REPROG_TITLE": "Quota Share with Exclusions Test",
        }
    ]
)

structures_df = pd.DataFrame(
    [
        {
            "BUSINESS_TITLE": "QS Aviation 25%",
            "INSPER_ID_PRE": 1,
            "INSPER_CONTRACT_ORDER": 1,
            "TYPE_OF_PARTICIPATION_CD": "quota_share",
            "INSPER_PREDECESSOR_TITLE": None,
            "INSPER_CLAIM_BASIS_CD": "risk_attaching",
            "INSPER_EFFECTIVE_DATE": "2024-01-01",
            "INSPER_EXPIRY_DATE": "2024-12-31",
        }
    ]
)

sections_df = pd.DataFrame(
    [
        {
            "INSPER_ID_PRE": 1,
            "BUSCL_EXCLUDE_CD": "exclude",
            "BUSCL_COUNTRY_CD": "Iran",
            "BUSCL_REGION": None,
            "BUSCL_CLASS_OF_BUSINESS_1": None,
            "BUSCL_CLASS_OF_BUSINESS_2": None,
            "BUSCL_CLASS_OF_BUSINESS_3": None,
            "BUSCL_LIMIT_CURRENCY_CD": None,
            "CESSION_PCT": None,
            "LIMIT_100": None,
            "ATTACHMENT_POINT_100": None,
            "SIGNED_SHARE_PCT": None,
        },
        {
            "INSPER_ID_PRE": 1,
            "BUSCL_EXCLUDE_CD": "exclude",
            "BUSCL_COUNTRY_CD": "Russia",
            "BUSCL_REGION": None,
            "BUSCL_CLASS_OF_BUSINESS_1": None,
            "BUSCL_CLASS_OF_BUSINESS_2": None,
            "BUSCL_CLASS_OF_BUSINESS_3": None,
            "BUSCL_LIMIT_CURRENCY_CD": None,
            "CESSION_PCT": None,
            "LIMIT_100": None,
            "ATTACHMENT_POINT_100": None,
            "SIGNED_SHARE_PCT": None,
        },
        {
            "INSPER_ID_PRE": 1,
            "BUSCL_EXCLUDE_CD": None,
            "BUSCL_COUNTRY_CD": None,
            "BUSCL_REGION": None,
            "BUSCL_CLASS_OF_BUSINESS_1": None,
            "BUSCL_CLASS_OF_BUSINESS_2": None,
            "BUSCL_CLASS_OF_BUSINESS_3": None,
            "BUSCL_LIMIT_CURRENCY_CD": None,
            "CESSION_PCT": 0.25,
            "LIMIT_100": None,
            "ATTACHMENT_POINT_100": None,
            "SIGNED_SHARE_PCT": 1.0,
        },
    ]
)

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    program_df.to_excel(writer, sheet_name="program", index=False)
    structures_df.to_excel(writer, sheet_name="structures", index=False)
    sections_df.to_excel(writer, sheet_name="sections", index=False)

print(f"✓ Programme créé: {output_file}")
print("\nStructure du programme:")
print("  - 1 structure: QS Aviation 25%")
print("  - 3 sections d'exclusion:")
print("    - Iran (pays)")
print("    - Russia (pays)")
print("  - 1 section normale: 25% cession sur tout le reste")
