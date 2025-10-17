# src/domain/constants.py
from types import SimpleNamespace

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
# Excel: noms des feuilles et colonnes
# ──────────────────────────────────────────────────────────────────────────────
SHEETS = (
    SimpleNamespace(  # PAd deja dans l'adapteur de excel ? Relation avec snowflake ?
        PROGRAM="program",
        STRUCTURES="structures",
        conditions="conditions",
    )
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
