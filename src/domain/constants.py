# src/domain/constants.py
from types import SimpleNamespace

# ──────────────────────────────────────────────────────────────────────────────
# Bordereau / colonnes d'entrée (CSV)
# ──────────────────────────────────────────────────────────────────────────────
FIELDS = {
    "POLICY_NUMBER": "policy_id",
    "INSURED_NAME": "INSURED_NAME",
    "COUNTRY": "BUSCL_COUNTRY_CD",
    "REGION": "BUSCL_REGION",
    "CLASS_1": "BUSCL_CLASS_OF_BUSINESS_1",
    "CLASS_2": "BUSCL_CLASS_OF_BUSINESS_2",
    "CLASS_3": "BUSCL_CLASS_OF_BUSINESS_3",
    "CURRENCY": "CURRENCY",
    "HULL_CURRENCY": "HULL_CURRENCY",
    "LIABILITY_CURRENCY": "LIABILITY_CURRENCY",
    "LINE_OF_BUSINESS": "line_of_business",
    "INDUSTRY": "industry",
    "SIC_CODE": "sic_code",
    "INCLUDE": "include",
    "EXPOSURE": "exposure",
    "INCEPTION_DATE": "INCEPTION_DT",
    "EXPIRY_DATE": "EXPIRE_DT",
}

# Seules les dimensions ci-dessous sont considérées au matching
DIMENSIONS = [
    "BUSCL_EXCLUDE_CD",
    "BUSCL_ENTITY_NAME_CED",
    "POL_RISK_NAME_CED",
    "BUSCL_COUNTRY_CD",
    "BUSCL_REGION",
    "BUSCL_CLASS_OF_BUSINESS_1",
    "BUSCL_CLASS_OF_BUSINESS_2",
    "BUSCL_CLASS_OF_BUSINESS_3",
    "CURRENCY",
    "HULL_CURRENCY",
    "LIABILITY_CURRENCY",
]

# ──────────────────────────────────────────────────────────────────────────────
# Underwriting Departments (valeurs possibles au niveau programme)
# ──────────────────────────────────────────────────────────────────────────────
UNDERWRITING_DEPARTMENT = SimpleNamespace(
    AVIATION="aviation",
    CASUALTY="casualty",
    TEST="test",
)
UNDERWRITING_DEPARTMENT_VALUES = {
    UNDERWRITING_DEPARTMENT.AVIATION,
    UNDERWRITING_DEPARTMENT.CASUALTY,
    UNDERWRITING_DEPARTMENT.TEST,
}

# ──────────────────────────────────────────────────────────────────────────────
# Types produits / claim basis (avec noms symboliques + ensembles de validation)
# ──────────────────────────────────────────────────────────────────────────────
PRODUCT = SimpleNamespace(
    QUOTA_SHARE="quota_share",
    EXCESS_OF_LOSS="excess_of_loss",
)
PRODUCT_TYPES = {PRODUCT.QUOTA_SHARE, PRODUCT.EXCESS_OF_LOSS}

CLAIM_BASIS = SimpleNamespace(
    RISK_ATTACHING="risk_attaching",
    LOSS_OCCURRING="loss_occurring",
)
CLAIM_BASIS_VALUES = {CLAIM_BASIS.RISK_ATTACHING, CLAIM_BASIS.LOSS_OCCURRING}

# ──────────────────────────────────────────────────────────────────────────────
# Currency validation by line of business (DEPRECATED - use dimension_mapping.py)
# ──────────────────────────────────────────────────────────────────────────────
# Note: These are kept for backward compatibility but should be replaced
# with the new dimension mapping system in dimension_mapping.py

CURRENCY_FIELDS = {
    "AVIATION_HULL": "HULL_CURRENCY",
    "AVIATION_LIABILITY": "LIABILITY_CURRENCY", 
    "CASUALTY": "CURRENCY",
}

CURRENCY_COLUMN_ALIASES = {
    "aviation": ["HULL_CURRENCY", "LIABILITY_CURRENCY"],
    "casualty": ["CURRENCY"],
}

# ──────────────────────────────────────────────────────────────────────────────
# Excel: noms des feuilles et colonnes
# ──────────────────────────────────────────────────────────────────────────────
SHEETS = SimpleNamespace(
    PROGRAM="program",
    STRUCTURES="structures",
    conditions="conditions",
)

PROGRAM_COLS = SimpleNamespace(
    TITLE="REPROG_TITLE",
    UNDERWRITING_DEPARTMENT="REPROG_UW_DEPARTMENT_LOB_CD",
)

STRUCTURE_COLS = SimpleNamespace(
    NAME="BUSINESS_TITLE",
    ORDER="INSPER_CONTRACT_ORDER",
    PREDECESSOR="INSPER_PREDECESSOR_TITLE",
    TYPE="TYPE_OF_PARTICIPATION_CD",
    CLAIM_BASIS="INSPER_CLAIM_BASIS_CD",
    INCEPTION="INSPER_EFFECTIVE_DATE",
    EXPIRY="INSPER_EXPIRY_DATE",
    INSPER_ID="INSPER_ID_PRE",
)

condition_COLS = SimpleNamespace(
    CESSION_PCT="CESSION_PCT",
    ATTACHMENT="ATTACHMENT_POINT_100",
    LIMIT="LIMIT_100",
    SIGNED_SHARE="SIGNED_SHARE_PCT",
    INCLUDES_HULL="INCLUDES_HULL",
    INCLUDES_LIABILITY="INCLUDES_LIABILITY",
)
