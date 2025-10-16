from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, Set, Optional, Literal, List

ColumnKind = Literal["dimension", "exposure", "meta"]


@dataclass(frozen=True)
class ColumnSpec:
    canonical: str
    kind: ColumnKind
    aliases: Set[str] = field(default_factory=set)
    required: bool = False
    required_by_lob: Dict[str, bool] = field(default_factory=dict)
    coerce: Optional[Callable] = None
    notes: str = ""


def _to_upper(x):
    if x is None:
        return x
    s = str(x)
    return s.upper()


def _to_date(x):
    import pandas as pd

    try:
        return pd.to_datetime(x)
    except Exception:
        return None


def _to_float(x):
    try:
        return float(x)
    except Exception:
        return None


# ——— Colonnes canoniques alignées avec l'engine ———
COLUMNS: Dict[str, ColumnSpec] = {
    # META / BASE
    "policy_id": ColumnSpec(
        "policy_id", "meta", aliases={"POLICY_ID", "policy_number", "POLICY_NUMBER"}
    ),
    "INSURED_NAME": ColumnSpec("INSURED_NAME", "meta", required=True, coerce=_to_upper),
    "INCEPTION_DT": ColumnSpec(
        "INCEPTION_DT",
        "meta",
        aliases={"INCEPTION_DATE"},
        required=True,
        coerce=_to_date,
    ),
    "EXPIRE_DT": ColumnSpec(
        "EXPIRE_DT", "meta", aliases={"EXPIRY_DATE"}, required=True, coerce=_to_date
    ),
    "line_of_business": ColumnSpec(
        "line_of_business", "meta", aliases={"LINE_OF_BUSINESS"}
    ),
    # DIMENSIONS
    "BUSCL_COUNTRY_CD": ColumnSpec("BUSCL_COUNTRY_CD", "dimension"),
    "BUSCL_REGION": ColumnSpec("BUSCL_REGION", "dimension"),
    "BUSCL_CLASS_OF_BUSINESS_1": ColumnSpec("BUSCL_CLASS_OF_BUSINESS_1", "dimension"),
    "BUSCL_CLASS_OF_BUSINESS_2": ColumnSpec("BUSCL_CLASS_OF_BUSINESS_2", "dimension"),
    "BUSCL_CLASS_OF_BUSINESS_3": ColumnSpec("BUSCL_CLASS_OF_BUSINESS_3", "dimension"),
    "BUSCL_ENTITY_NAME_CED": ColumnSpec("BUSCL_ENTITY_NAME_CED", "dimension"),
    "POL_RISK_NAME_CED": ColumnSpec("POL_RISK_NAME_CED", "dimension"),
    "BUSCL_EXCLUDE_CD": ColumnSpec("BUSCL_EXCLUDE_CD", "dimension"),
    # currency (dimension logique unique ; représentation selon LOB)
    "CURRENCY": ColumnSpec(
        "CURRENCY", "dimension", aliases={"BUSCL_LIMIT_CURRENCY_CD"}
    ),
    "HULL_CURRENCY": ColumnSpec("HULL_CURRENCY", "dimension"),
    "LIABILITY_CURRENCY": ColumnSpec("LIABILITY_CURRENCY", "dimension"),
    # EXPOSURE — Casualty
    "LIMIT": ColumnSpec(
        "LIMIT", "exposure", required_by_lob={"casualty": True}, coerce=_to_float
    ),
    "CEDENT_SHARE": ColumnSpec(
        "CEDENT_SHARE", "exposure", required_by_lob={"casualty": True}, coerce=_to_float
    ),
    # EXPOSURE — Aviation
    "HULL_LIMIT": ColumnSpec(
        "HULL_LIMIT", "exposure", required_by_lob={"aviation": False}, coerce=_to_float
    ),
    "HULL_SHARE": ColumnSpec(
        "HULL_SHARE", "exposure", required_by_lob={"aviation": False}, coerce=_to_float
    ),
    "LIABILITY_LIMIT": ColumnSpec(
        "LIABILITY_LIMIT",
        "exposure",
        required_by_lob={"aviation": False},
        coerce=_to_float,
    ),
    "LIABILITY_SHARE": ColumnSpec(
        "LIABILITY_SHARE",
        "exposure",
        required_by_lob={"aviation": False},
        coerce=_to_float,
    ),
    # EXPOSURE — Test
    "exposure": ColumnSpec(
        "exposure", "exposure", required_by_lob={"test": True}, coerce=_to_float
    ),
}


# ——— Règles d'exposition par LOB (déclaratives) ———
def exposure_rules_for_lob(lob: str) -> Dict[str, str]:
    if not lob:
        return {}
    lob = lob.lower()
    if lob == "aviation":
        return {
            "at_least_one_of": "HULL_LIMIT|LIABILITY_LIMIT",
            "pairs": "HULL_LIMIT<->HULL_SHARE;LIABILITY_LIMIT<->LIABILITY_SHARE",
        }
    if lob in ("casualty", "test"):
        return {}
    return {}


# ——— Mapping Program -> Bordereau (source de vérité unique) ———
PROGRAM_TO_BORDEREAU_DIMENSIONS: Dict[str, object] = {
    # identiques
    "BUSCL_COUNTRY_CD": "BUSCL_COUNTRY_CD",
    "BUSCL_REGION": "BUSCL_REGION",
    "BUSCL_CLASS_OF_BUSINESS_1": "BUSCL_CLASS_OF_BUSINESS_1",
    "BUSCL_CLASS_OF_BUSINESS_2": "BUSCL_CLASS_OF_BUSINESS_2",
    "BUSCL_CLASS_OF_BUSINESS_3": "BUSCL_CLASS_OF_BUSINESS_3",
    "BUSCL_ENTITY_NAME_CED": "BUSCL_ENTITY_NAME_CED",
    "POL_RISK_NAME_CED": "POL_RISK_NAME_CED",
    "BUSCL_EXCLUDE_CD": "BUSCL_EXCLUDE_CD",
    # currency logique unique -> dépend du LOB
    "BUSCL_LIMIT_CURRENCY_CD": {
        "aviation": "HULL_CURRENCY",
        "casualty": "CURRENCY",
        "test": "CURRENCY",
    },
}


# ——— Helpers normalisation ———
def build_alias_to_canonical() -> Dict[str, str]:
    m: Dict[str, str] = {}
    for canon, spec in COLUMNS.items():
        for alias in spec.aliases:
            m[alias] = canon
    return m


def get_all_mappable_dimensions(
    bordereau_columns: List[str], uw_dept: Optional[str]
) -> Dict[str, str]:
    """
    Retourne le mapping des dimensions de programme vers les colonnes de bordereau
    pour les dimensions présentes dans le bordereau.

    Args:
        bordereau_columns: Liste des colonnes disponibles dans le bordereau
        uw_dept: Département underwriting (aviation, casualty, test)

    Returns:
        Dict mapping dimension_programme -> colonne_bordereau
    """
    out: Dict[str, str] = {}
    for dim, mapping in PROGRAM_TO_BORDEREAU_DIMENSIONS.items():
        if isinstance(mapping, str):
            if mapping in bordereau_columns:
                out[dim] = mapping
        elif isinstance(mapping, dict):
            if uw_dept in mapping:
                m = mapping[uw_dept]
                if m in bordereau_columns:
                    out[dim] = m
    return out
