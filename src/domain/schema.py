from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, Set, Optional, Literal, List, Union

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
    "policy_id": ColumnSpec("policy_id", "meta"),
    "INSURED_NAME": ColumnSpec("INSURED_NAME", "meta", required=True, coerce=_to_upper),
    "INCEPTION_DT": ColumnSpec(
        "INCEPTION_DT",
        "meta",
        required=True,
        coerce=_to_date,
    ),
    "EXPIRE_DT": ColumnSpec("EXPIRE_DT", "meta", required=True, coerce=_to_date),
    "line_of_business": ColumnSpec("line_of_business", "meta"),
    # Dimension mappings
    "COUNTRY": ColumnSpec("COUNTRIES", "dimension"),
    "REGION": ColumnSpec("REGION", "dimension"),
    "PRODUCT_TYPE_LEVEL_1": ColumnSpec("PRODUCT_TYPE_LEVEL_1", "dimension"),
    "PRODUCT_TYPE_LEVEL_2": ColumnSpec("PRODUCT_TYPE_LEVEL_2", "dimension"),
    "PRODUCT_TYPE_LEVEL_3": ColumnSpec("PRODUCT_TYPE_LEVEL_3", "dimension"),
    "BUSCL_ENTITY_NAME_CED": ColumnSpec("BUSCL_ENTITY_NAME_CED", "dimension"),
    "POL_RISK_NAME_CED": ColumnSpec("POL_RISK_NAME_CED", "dimension"),
    # currency (dimension logique unique ; représentation selon LOB)
    "ORIGINAL_CURRENCY": ColumnSpec("ORIGINAL_CURRENCY", "dimension"),
    "HULL_CURRENCY": ColumnSpec("HULL_CURRENCY", "dimension"),
    "LIAB_CURRENCY": ColumnSpec("LIAB_CURRENCY", "dimension"),
    # EXPOSURE — Casualty
    "OCCURRENCE_LIMIT_100_ORIG": ColumnSpec(
        "OCCURRENCE_LIMIT_100_ORIG", "exposure", required_by_lob={"casualty": True}, coerce=_to_float
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
    "LIAB_LIMIT": ColumnSpec(
        "LIAB_LIMIT",
        "exposure",
        required_by_lob={"aviation": False},
        coerce=_to_float,
    ),
    "LIAB_SHARE": ColumnSpec(
        "LIAB_SHARE",
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
            "at_least_one_of": "HULL_LIMIT|LIAB_LIMIT",
            "pairs": "HULL_LIMIT<->HULL_SHARE;LIAB_LIMIT<->LIAB_SHARE",
        }
    if lob in ("casualty", "test"):
        return {}
    return {}


# ——— Mapping Program -> Bordereau (source de vérité unique) ———
# Mapping "clés builder" -> "colonne Snowflake" (ou map par LOB)
# Les clés builder correspondent aux champs produits par build_condition(...)
PROGRAM_TO_BORDEREAU_DIMENSIONS: Dict[str, Union[str, Dict[str, str]]] = {
    "COUNTRY": "COUNTRY",
    "REGION": "REGION",
    "PRODUCT_TYPE_LEVEL_1": "PRODUCT_TYPE_LEVEL_1",
    "PRODUCT_TYPE_LEVEL_2": "PRODUCT_TYPE_LEVEL_2",
    "PRODUCT_TYPE_LEVEL_3": "PRODUCT_TYPE_LEVEL_3",
    "CURRENCY": {
        "aviation": "HULL_CURRENCY",
        "casualty": "ORIGINAL_CURRENCY"
    },
}


# --- Dimension mapping hub (single source of truth) --------------------------
from typing import Optional, Dict, List, Set, Literal, Iterable, Union
import pandas as pd

# Alias sémantique: on garde PROGRAM_TO_BORDEREAU_DIMENSIONS comme mapping canonique
# builder_key -> colonne physique (string) OU dict par LOB
DIMENSION_REGISTRY: Dict[str, Union[str, Dict[str, str]]] = PROGRAM_TO_BORDEREAU_DIMENSIONS

# Certains "flags" se baladent avec les dimensions côté conditions
DIM_FLAGS: Set[str] = {"INCLUDES_HULL", "INCLUDES_LIABILITY"}


def _choose_for_lob(val: Union[str, Dict[str, str]], uw_dept: Optional[str]) -> str:
    """Sélectionne la colonne physique correspondant au LOB (fallback: premier item)."""
    if isinstance(val, str):
        return val
    lob = (uw_dept or "").lower()
    if lob in val:
        return val[lob]
    # fallback stable si le LOB n'est pas dans le dict
    return next(iter(val.values()))


def builder_to_physical_map(
    uw_dept: Optional[str],
    *,
    target: Literal["snowflake", "bordereau"] = "snowflake",
) -> Dict[str, str]:
    """
    Map {dimension_builder -> nom_de_colonne_physique} pour un LOB.
    Aujourd'hui snowflake == bordereau côté noms physiques; 'target' est là pour évoluer.
    """
    out: Dict[str, str] = {}
    for k, v in DIMENSION_REGISTRY.items():
        out[k] = _choose_for_lob(v, uw_dept)
    return out


def physical_to_builder_map(
    uw_dept: Optional[str],
    *,
    target: Literal["snowflake", "bordereau"] = "snowflake",
) -> Dict[str, str]:
    """Inverse de builder_to_physical_map: {col_physique -> dimension_builder}."""
    fwd = builder_to_physical_map(uw_dept, target=target)
    return {phys: builder for builder, phys in fwd.items()}


def resolve_bordereau_column(dim_key: str, uw_dept: Optional[str]) -> Optional[str]:
    """Donne la colonne de bordereau (physique) qui correspond à une dimension logique."""
    return builder_to_physical_map(uw_dept, target="bordereau").get(dim_key)


def physical_dim_names(*, include_flags: bool = False) -> Set[str]:
    """Ensemble des noms de colonnes 'physiques' possibles (tous LOB confondus)."""
    names: Set[str] = set()
    for v in DIMENSION_REGISTRY.values():
        if isinstance(v, dict):
            names.update(v.values())
        else:
            names.add(v)
    if include_flags:
        names |= DIM_FLAGS
    return names


def dims_in(df: pd.DataFrame, *, include_flags: bool = False) -> List[str]:
    """Liste ordonnée des colonnes 'dimension' présentes dans un DF de conditions/exclusions (physiques)."""
    if df is None or df.empty:
        return []
    phys = physical_dim_names(include_flags=include_flags)
    return [c for c in df.columns if c in phys]


def present_bordereau_mapping(
    bordereau_columns: Iterable[str], uw_dept: Optional[str]
) -> Dict[str, str]:
    """
    {dimension_builder -> colonne_bordereau_physique} pour les dimensions VRAIMENT présentes
    dans un bordereau donné.
    """
    cols = set(bordereau_columns)
    mp = builder_to_physical_map(uw_dept, target="bordereau")
    return {k: v for k, v in mp.items() if v in cols}


# Back-compat du helper public déjà exposé (utilisé par Bordereau.dimension_mapping)
def get_all_mappable_dimensions(
    bordereau_columns: List[str], uw_dept: Optional[str]
) -> Dict[str, str]:
    return present_bordereau_mapping(bordereau_columns, uw_dept)
