# src/domain/constants.py
from types import SimpleNamespace

# ──────────────────────────────────────────────────────────────────────────────
# Underwriting Departments (valeurs possibles au niveau programme)
# ──────────────────────────────────────────────────────────────────────────────
UW_DEPARTMENT_CODE = SimpleNamespace(
    AVIATION="aviation",
    CASUALTY="casualty",
    TEST="test",
)
UNDERWRITING_DEPARTMENT_VALUES = {
    UW_DEPARTMENT_CODE.AVIATION,
    UW_DEPARTMENT_CODE.CASUALTY,
    UW_DEPARTMENT_CODE.TEST,
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
        EXCLUSIONS="exclusions",
    )
)

PROGRAM_COLS = SimpleNamespace(
    TITLE="TITLE",
    UW_DEPARTMENT_CODE="UW_LOB_ID", # AURE : pas certains si c'est le bon nom de colonne
    MAIN_CURRENCY="MAIN_CURRENCY_ID",
)

STRUCTURE_COLS = SimpleNamespace(
    NAME="RP_STRUCTURE_NAME",
    PREDECESSOR="RP_STRUCTURE_ID_PREDECESSOR",
    TYPE="TYPE_OF_PARTICIPATION",
    CLAIM_BASIS="CLAIMS_BASIS",
    INCEPTION="EFFECTIVE_DATE",
    EXPIRY="EXPIRY_DATE",
    INSPER_ID="RP_STRUCTURE_ID",  # Clé primaire auto-increment Snowflake
)

CONDITION_COLS = SimpleNamespace(
    CESSION_PCT="CESSION_PCT",
    ATTACHMENT="ATTACHMENT_POINT_100",
    LIMIT="LIMIT_100",
    SIGNED_SHARE="SIGNED_SHARE_PCT",
    INCLUDES_HULL="INCLUDES_HULL",
    INCLUDES_LIABILITY="INCLUDES_LIABILITY",
    INSPER_ID="INSPER_ID_PRE",  # ID de liaison vers les structures (gardé pour compatibilité)
)
