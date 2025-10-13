"""
Créer un programme de test pour le test d'intégration grandeur réelle.
Programme: QS 30% → XL 50M xs 20M
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pandas as pd
from examples.program_creation.excel_utils import create_excel_with_auto_width


def create_test_program_qs_xl():
    output_path = Path(__file__).parent / "test_program_qs_xl.xlsx"
    
    # 1. PROGRAM sheet
    program_df = pd.DataFrame([{
        "REPROG_ID_PRE": 1,
        "REPROG_TITLE": "TEST_QS_XL",
        "REPROG_ENTITY_NAME_CED": "TEST_CEDANT",
        "REPROG_REGION": None,
        "REPROG_COUNTRY_CD": None,
        "REPROG_CLASS_OF_BUSINESS_1": None,
        "REPROG_CLASS_OF_BUSINESS_2": None,
        "REPROG_CLASS_OF_BUSINESS_3": None,
        "REPROG_LIMIT_CURRENCY_CD": None,
        "REPROG_LOB_CD": None,
        "REPROG_UNDERWRITING_YEAR": 2024,
        "REPROG_INCEPTION_DATE": "2024-01-01",
        "REPROG_EXPIRY_DATE": "2025-01-01",
        "REPROG_MANAGEMENT_REPORTING_LOB_CD": None,
    }])
    
    # 2. STRUCTURES sheet
    structures_df = pd.DataFrame([
        {
            "INSPER_ID_PRE": 1,
            "BUSINESS_ID_PRE": None,
            "BUSINESS_TITLE": "QS_30%",
            "INSPER_CONTRACT_ORDER": 1,
            "INSPER_PREDECESSOR_TITLE": None,
            "TYPE_OF_PARTICIPATION_CD": "quota_share",
            "INSPER_CLAIM_BASIS_CD": "risk_attaching",
            "INSPER_EFFECTIVE_DATE": "2024-01-01",
            "INSPER_EXPIRY_DATE": "2025-01-01",
            "INSPER_TERRORISM_COVERAGE_CD": None,
            "INSPER_NUMBER_OF_LINES": None,
            "INSPER_SHARE_OF_ORIGINAL_LINE_PERC": None,
            "INSPER_SIGNED_LINE_PERCENTAGE": None,
            "INSPER_AAD_AMOUNT": None,
            "INSPER_AAL_AMOUNT": None,
            "INSPER_TERRORISM_AAL_AMOUNT": None,
            "INSPER_FREE_LIMIT_AMOUNT": None,
            "INSPER_TERRORISM_FREE_LIMIT_AMOUNT": None,
            "INSPER_LOD_TO_RA_DATE_SLAV": None,
            "INSPER_COMMENT": None,
        },
        {
            "INSPER_ID_PRE": 2,
            "BUSINESS_ID_PRE": None,
            "BUSINESS_TITLE": "XOL_50xs20",
            "INSPER_CONTRACT_ORDER": 2,
            "INSPER_PREDECESSOR_TITLE": "QS_30%",
            "TYPE_OF_PARTICIPATION_CD": "excess_of_loss",
            "INSPER_CLAIM_BASIS_CD": "risk_attaching",
            "INSPER_EFFECTIVE_DATE": "2024-01-01",
            "INSPER_EXPIRY_DATE": "2025-01-01",
            "INSPER_TERRORISM_COVERAGE_CD": None,
            "INSPER_NUMBER_OF_LINES": None,
            "INSPER_SHARE_OF_ORIGINAL_LINE_PERC": None,
            "INSPER_SIGNED_LINE_PERCENTAGE": None,
            "INSPER_AAD_AMOUNT": None,
            "INSPER_AAL_AMOUNT": None,
            "INSPER_TERRORISM_AAL_AMOUNT": None,
            "INSPER_FREE_LIMIT_AMOUNT": None,
            "INSPER_TERRORISM_FREE_LIMIT_AMOUNT": None,
            "INSPER_LOD_TO_RA_DATE_SLAV": None,
            "INSPER_COMMENT": None,
        }
    ])
    
    # 3. SECTIONS sheet
    sections_df = pd.DataFrame([
        # QS 30% section - applies to all
        {
            "BUSCL_ID_PRE": 1,
            "REPROG_ID_PRE": 1,
            "INSPER_ID_PRE": 1,
            "BUSINESS_ID_PRE": None,
            "BUSCL_EXCLUDE_CD": None,
            "BUSCL_ENTITY_NAME_CED": None,
            "POL_RISK_NAME_CED": None,
            "BUSCL_COUNTRY_CD": None,
            "BUSCL_REGION": None,
            "BUSCL_CLASS_OF_BUSINESS_1": None,
            "BUSCL_CLASS_OF_BUSINESS_2": None,
            "BUSCL_CLASS_OF_BUSINESS_3": None,
            "BUSCL_LIMIT_CURRENCY_CD": None,
            "CESSION_PCT": 0.30,
            "ATTACHMENT_POINT_100": None,
            "LIMIT_100": None,
            "SIGNED_SHARE_PCT": 1.00,
            "BUSCL_PREMIUM_RATE": None,
            "BUSCL_MIN_PREMIUM": None,
            "BUSCL_DEPOSIT_PREMIUM": None,
            "BUSCL_COMMENT": None,
            "BUSCL_TREATY_SHARE_PCT": None,
            "BUSCL_BROKER_REF": None,
            "BUSCL_BROKER": None,
            "BUSCL_REINSURER": None,
            "BUSCL_REINSURER_REF": None,
            "BUSCL_REINSURER_DOMICILE": None,
            "BUSCL_REINSURER_TYPE_CD": None,
            "BUSCL_REINSURER_CONTACT_NAME": None,
            "BUSCL_RISK_CODE": None,
            "BUSCL_RDS_CODE": None,
            "BUSCL_REINSTATEMENTS": None,
            "BUSCL_FREE_REINSTATEMENTS": None,
            "BUSCL_AAD_BASIS_CD": None,
            "BUSCL_AAL_BASIS_CD": None,
            "LIMIT_EVENT": None,
            "NO_OF_REINSTATEMENTS": None,
        },
        # XL 50M xs 20M section - applies to all
        {
            "BUSCL_ID_PRE": 2,
            "REPROG_ID_PRE": 1,
            "INSPER_ID_PRE": 2,
            "BUSINESS_ID_PRE": None,
            "BUSCL_EXCLUDE_CD": None,
            "BUSCL_ENTITY_NAME_CED": None,
            "POL_RISK_NAME_CED": None,
            "BUSCL_COUNTRY_CD": None,
            "BUSCL_REGION": None,
            "BUSCL_CLASS_OF_BUSINESS_1": None,
            "BUSCL_CLASS_OF_BUSINESS_2": None,
            "BUSCL_CLASS_OF_BUSINESS_3": None,
            "BUSCL_LIMIT_CURRENCY_CD": None,
            "CESSION_PCT": None,
            "ATTACHMENT_POINT_100": 20_000_000,
            "LIMIT_100": 50_000_000,
            "SIGNED_SHARE_PCT": 1.00,
            "BUSCL_PREMIUM_RATE": None,
            "BUSCL_MIN_PREMIUM": None,
            "BUSCL_DEPOSIT_PREMIUM": None,
            "BUSCL_COMMENT": None,
            "BUSCL_TREATY_SHARE_PCT": None,
            "BUSCL_BROKER_REF": None,
            "BUSCL_BROKER": None,
            "BUSCL_REINSURER": None,
            "BUSCL_REINSURER_REF": None,
            "BUSCL_REINSURER_DOMICILE": None,
            "BUSCL_REINSURER_TYPE_CD": None,
            "BUSCL_REINSURER_CONTACT_NAME": None,
            "BUSCL_RISK_CODE": None,
            "BUSCL_RDS_CODE": None,
            "BUSCL_REINSTATEMENTS": None,
            "BUSCL_FREE_REINSTATEMENTS": None,
            "BUSCL_AAD_BASIS_CD": None,
            "BUSCL_AAL_BASIS_CD": None,
            "LIMIT_EVENT": None,
            "NO_OF_REINSTATEMENTS": None,
        }
    ])
    
    create_excel_with_auto_width(
        str(output_path),
        {
            "program": program_df,
            "structures": structures_df,
            "sections": sections_df
        }
    )
    
    print(f"✓ Programme de test créé: {output_path}")
    print("\nSTRUCTURE:")
    print("  1. QS_30%: Quota Share 30% (reinsurer share 100%)")
    print("  2. XOL_50xs20: Excess of Loss 50M xs 20M (reinsurer share 100%)")
    print("     └─ Inuring sur QS_30% (rescaling automatique)")
    
    return output_path


if __name__ == "__main__":
    create_test_program_qs_xl()

