from __future__ import annotations
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from src.domain import Program, Structure
from src.domain.exclusion import ExclusionRule
from src.domain.constants import (
    PROGRAM_COLS,
    STRUCTURE_COLS,
    condition_COLS,
    CLAIM_BASIS_VALUES,
)
from src.domain.schema import PROGRAM_TO_BORDEREAU_DIMENSIONS
from .codecs import to_bool, split_multi, pandas_to_native, MULTI_VALUE_SEPARATOR
from .program_frames import ProgramFrames, condition_dims_in, exclusion_dims_in


class ProgramSerializer:
    """Ne gère plus que :
    - DataFrames -> objets domaine
    - objets domaine -> DataFrames canoniques (lean ou full)
    L'encodage multi-valeurs et la compaction sont mutualisés ailleurs.
    """

    # ---------- Import (DFs -> Domain) ----------
    def dataframes_to_program(
        self,
        program_df: pd.DataFrame,
        structures_df: pd.DataFrame,
        conditions_df: pd.DataFrame,
        exclusions_df: Optional[pd.DataFrame] = None,
    ) -> Program:

        name = pandas_to_native(program_df.iloc[0][PROGRAM_COLS.TITLE])
        uw_dept = pandas_to_native(
            program_df.iloc[0].get(PROGRAM_COLS.UW_DEPARTMENT_CODE)
        )
        if not uw_dept:
            raise ValueError(
                f"Underwriting department is mandatory for program '{name}'."
            )

        # flags booléens (si présents)
        for col in ("INCLUDES_HULL", "INCLUDES_LIABILITY"):
            if col in conditions_df.columns:
                conditions_df[col] = conditions_df[col].map(to_bool, na_action="ignore")

        # Aviation → flags requis et non nuls
        if str(uw_dept).lower() == "aviation":
            for col in ("INCLUDES_HULL", "INCLUDES_LIABILITY"):
                if col not in conditions_df.columns:
                    raise ValueError(f"Column {col} is required for Aviation programs.")
                if conditions_df[col].isna().any():
                    raise ValueError(
                        f"Column {col} contains nulls for Aviation program."
                    )

        # Dimensions → listes
        dims = condition_dims_in(conditions_df)
        for col in dims:
            conditions_df[col] = conditions_df[col].map(split_multi, na_action="ignore")

        # Structures: présence & valeurs minimales
        req = [
            STRUCTURE_COLS.INSPER_ID,
            STRUCTURE_COLS.CLAIM_BASIS,
            STRUCTURE_COLS.INCEPTION,
            STRUCTURE_COLS.EXPIRY,
            STRUCTURE_COLS.NAME,
            STRUCTURE_COLS.TYPE,
        ]
        for col in req:
            if col not in structures_df.columns:
                raise ValueError(f"Missing required column in 'structures': {col}")

        bad = []
        for i, row in structures_df.iterrows():
            cb = (
                str(row[STRUCTURE_COLS.CLAIM_BASIS]).strip().lower()
                if pd.notna(row[STRUCTURE_COLS.CLAIM_BASIS])
                else ""
            )
            if (
                (cb not in CLAIM_BASIS_VALUES)
                or pd.isna(row[STRUCTURE_COLS.INCEPTION])
                or pd.isna(row[STRUCTURE_COLS.EXPIRY])
            ):
                bad.append(i)
        if bad:
            raise ValueError(
                f"'structures' has {len(bad)} invalid row(s) for claim_basis/effective/expiry. Rows: {bad[:10]}{'...' if len(bad)>10 else ''}"
            )

        # Build domain
        def df_to_dicts(df: pd.DataFrame) -> List[Dict[str, Any]]:
            recs = df.to_dict("records")
            return [{k: pandas_to_native(v) for k, v in r.items()} for r in recs]

        conditions_by_structure: Dict[Any, List[Dict[str, Any]]] = {}
        for cond in df_to_dicts(conditions_df):
            key = cond.get(condition_COLS.INSPER_ID)
            if key is None:
                raise ValueError("INSPER_ID_PRE is mandatory for all conditions.")
            conditions_by_structure.setdefault(key, []).append(cond)

        structures: List[Structure] = []
        for s in df_to_dicts(structures_df):
            key = s.get(STRUCTURE_COLS.INSPER_ID)
            if key is None:
                raise ValueError("INSPER_ID_PRE is mandatory for all structures.")
            conds = conditions_by_structure.get(key, [])
            structures.append(Structure.from_row(s, conds, STRUCTURE_COLS))

        # Exclusions
        exclusions: List[ExclusionRule] = []
        prog_dims = list(PROGRAM_TO_BORDEREAU_DIMENSIONS.keys())
        if exclusions_df is not None and not exclusions_df.empty:
            ex_df = exclusions_df.copy()
            keep = set(prog_dims) | {
                "EXCLUSION_NAME",
                "EXCL_EFFECTIVE_DATE",
                "EXCL_EXPIRY_DATE",
            }
            ex_df = ex_df[[c for c in ex_df.columns if c in keep]]
            for d in prog_dims:
                if d in ex_df.columns:
                    ex_df[d] = ex_df[d].map(split_multi, na_action="ignore")
            for row in ex_df.to_dict("records"):
                exclusions.append(ExclusionRule.from_row(row, prog_dims))

        return Program(
            name=name,
            structures=structures,
            dimension_columns=dims,
            underwriting_department=uw_dept,
            exclusions=exclusions,
        )

    # ---------- Export (Domain -> Frames) ----------
    def program_to_dataframes(
        self, program: Program, *, lean: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """Par défaut: export 'lean' (colonnes essentielles). On garde l'API actuelle."""

        program_df = pd.DataFrame(
            {
                "TITLE": [program.name],
                "UW_LOB": [program.underwriting_department],
                "ACTIVE_IND": [True],  # Colonne requise par Snowflake
            }
        )

        structures_rows, conditions_rows = [], []
        insper = 1
        for st in program.structures:
            structures_rows.append(
                {
                    "RP_STRUCTURE_ID": insper,
                    "RP_STRUCTURE_NAME": st.structure_name,
                    "TYPE_OF_PARTICIPATION": st.type_of_participation,
                    "PREDECESSOR_TITLE": st.predecessor_title,
                    "CLAIMS_BASIS": st.claim_basis,
                    "EFFECTIVE_DATE": st.inception_date,
                    "EXPIRY_DATE": st.expiry_date,
                }
            )
            for c in st.conditions:
                d = c.to_dict()
                row = {
                    "INSPER_ID_PRE": insper,
                    "CESSION_PCT": d.get("CESSION_PCT"),
                    "LIMIT_100": d.get("LIMIT_100"),
                    "ATTACHMENT_POINT_100": d.get("ATTACHMENT_POINT_100"),
                    "SIGNED_SHARE_PCT": d.get("SIGNED_SHARE_PCT"),
                    "INCLUDES_HULL": d.get("INCLUDES_HULL"),
                    "INCLUDES_LIABILITY": d.get("INCLUDES_LIABILITY"),
                }
                for dim in program.dimension_columns:
                    row[dim] = d.get(dim)
                conditions_rows.append(row)
            insper += 1

        exclusions_df = self._exclusions_to_df(program)
        return {
            "program": program_df,
            "structures": pd.DataFrame(structures_rows),
            "conditions": pd.DataFrame(conditions_rows),
            "exclusions": exclusions_df,
        }

    def _exclusions_to_df(self, program: Program) -> pd.DataFrame:
        if not program.exclusions:
            # Colonnes par défaut avec mapping Snowflake
            default_cols = [
                "EXCLUSION_NAME",
                "EXCL_EFFECTIVE_DATE", 
                "EXCL_EXPIRY_DATE",
            ]
            for d in PROGRAM_TO_BORDEREAU_DIMENSIONS.keys():
                if d == "BUSCL_ENTITY_NAME_CED":
                    default_cols.append("ENTITY_NAME_CED")
                elif d == "POL_RISK_NAME_CED":
                    default_cols.append("RISK_NAME")
                else:
                    default_cols.append(d)
            return pd.DataFrame(columns=default_cols)
        rows = []
        for e in program.exclusions:
            row = {
                "EXCLUSION_NAME": e.name,
                "EXCL_EFFECTIVE_DATE": e.effective_date,
                "EXCL_EXPIRY_DATE": e.expiry_date,
            }
            for d in PROGRAM_TO_BORDEREAU_DIMENSIONS.keys():
                vals = e.values_by_dimension.get(d)
                # Mapping pour les exclusions vers les noms Snowflake
                if d == "BUSCL_ENTITY_NAME_CED":
                    row["ENTITY_NAME_CED"] = MULTI_VALUE_SEPARATOR.join(vals) if vals else None
                elif d == "POL_RISK_NAME_CED":
                    row["RISK_NAME"] = MULTI_VALUE_SEPARATOR.join(vals) if vals else None
                else:
                    row[d] = MULTI_VALUE_SEPARATOR.join(vals) if vals else None
            rows.append(row)
        return pd.DataFrame(rows)
