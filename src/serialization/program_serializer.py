from __future__ import annotations
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from src.domain import Program, Structure
from src.domain.exclusion import ExclusionRule
from src.domain.constants import (
    PROGRAM_COLS,
    STRUCTURE_COLS,
    CONDITION_COLS,
    CLAIM_BASIS_VALUES,
)
from src.domain.schema import (
    PROGRAM_TO_BORDEREAU_DIMENSIONS,
    builder_to_physical_map,
    physical_to_builder_map,
    dims_in,
)
from .codecs import to_bool, split_multi, pandas_to_native


# Helpers mapping dims - maintenant centralisés dans schema.py


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
        field_links_df: Optional[pd.DataFrame] = None,
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

        # Dimensions (Snowflake) → listes
        # 1) split sur colonnes Snowflake (COUNTRY_ID, ...)
        snow_dims = dims_in(conditions_df)
        for col in snow_dims:
            conditions_df[col] = conditions_df[col].map(split_multi, na_action="ignore")

        # 2) renommer Snowflake → builder pour construire le domaine
        inv_map = physical_to_builder_map(uw_dept)
        conditions_df = conditions_df.rename(columns={k: v for k, v in inv_map.items() if k in conditions_df.columns})

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

        # Nouvelle architecture : reconstruire les structures avec leurs conditions via field_links_df
        structures: List[Structure] = []
        
        # Créer un mapping des conditions par RP_CONDITION_ID
        conditions_by_id = {}
        for cond in df_to_dicts(conditions_df):
            condition_id = cond.get("RP_CONDITION_ID")
            if condition_id is not None:
                conditions_by_id[condition_id] = cond
        
        # Créer un mapping des field_links par RP_STRUCTURE_ID
        field_links_by_structure = {}
        if field_links_df is not None and not field_links_df.empty:
            for link in df_to_dicts(field_links_df):
                structure_id = link.get("RP_STRUCTURE_ID")
                condition_id = link.get("RP_CONDITION_ID")
                field_name = link.get("FIELD_NAME")
                new_value = link.get("NEW_VALUE")
                
                if structure_id not in field_links_by_structure:
                    field_links_by_structure[structure_id] = {}
                if condition_id not in field_links_by_structure[structure_id]:
                    field_links_by_structure[structure_id][condition_id] = {}
                
                field_links_by_structure[structure_id][condition_id][field_name] = new_value
        
        # Reconstruire les structures
        for s in df_to_dicts(structures_df):
            structure_id = s.get(STRUCTURE_COLS.INSPER_ID)
            if structure_id is None:
                raise ValueError("RP_STRUCTURE_ID is mandatory for all structures.")
            
            # Trouver les conditions liées à cette structure via field_links
            linked_conditions = []
            if structure_id in field_links_by_structure:
                for condition_id, overrides in field_links_by_structure[structure_id].items():
                    if condition_id in conditions_by_id:
                        # Créer une condition avec les valeurs par défaut de la structure
                        condition = conditions_by_id[condition_id].copy()
                        
                        # Appliquer les valeurs par défaut de la structure d'abord
                        condition[CONDITION_COLS.CESSION_PCT] = s.get("CESSION_PCT")
                        condition[CONDITION_COLS.ATTACHMENT] = s.get("ATTACHMENT_POINT_100")
                        condition[CONDITION_COLS.LIMIT] = s.get("LIMIT_100")
                        condition[CONDITION_COLS.SIGNED_SHARE] = s.get("SIGNED_SHARE_PCT")
                        
                        # Puis appliquer les overrides financiers
                        for field_name, new_value in overrides.items():
                            condition[field_name] = new_value
                        
                        linked_conditions.append(condition)
            
            # Ne pas créer automatiquement une condition par défaut
            # Les valeurs par défaut restent dans la structure elle-même
            # linked_conditions reste vide si aucune condition spécifique
            
            # Créer la structure avec ses conditions
            structures.append(Structure.from_row(s, linked_conditions, STRUCTURE_COLS))

        # Exclusions
        exclusions: List[ExclusionRule] = []
        prog_dims_builder = list(PROGRAM_TO_BORDEREAU_DIMENSIONS.keys())
        if exclusions_df is not None and not exclusions_df.empty:
            ex_df = exclusions_df.copy()

            # split sur dims Snowflake
            for col in dims_in(ex_df):
                ex_df[col] = ex_df[col].map(split_multi, na_action="ignore")

            # renommer Snowflake -> builder
            ex_df = ex_df.rename(columns={k: v for k, v in inv_map.items() if k in ex_df.columns})

            keep = set(prog_dims_builder) | {"EXCLUSION_NAME", "EXCL_EFFECTIVE_DATE", "EXCL_EXPIRY_DATE"}
            ex_df = ex_df[[c for c in ex_df.columns if c in keep]]

            for row in ex_df.to_dict("records"):
                exclusions.append(ExclusionRule.from_row(row, prog_dims_builder))

        return Program(
            name=name,
            structures=structures,
            dimension_columns=prog_dims_builder,
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
                "UW_LOB_ID": [program.underwriting_department],
                "ACTIVE_IND": [True],  # Colonne requise par Snowflake
            }
        )

        structures_rows, conditions_rows, field_links_rows = [], [], []

        # Pool global de conditions uniques : signature -> RP_CONDITION_ID
        pool: dict[tuple, int] = {}
        next_condition_id = 1

        # Signature -> row Snowflake (une seule fois par signature)
        unique_condition_rows: dict[tuple, dict] = {}

        insper = 1
        for st in program.structures:
            # 1) Structure (défauts financiers au niveau structure)
            structures_rows.append({
                "RP_STRUCTURE_ID": insper,
                "RP_STRUCTURE_NAME": st.structure_name,
                "TYPE_OF_PARTICIPATION": st.type_of_participation,
                "RP_STRUCTURE_ID_PREDECESSOR": st.predecessor_title,
                "CLAIMS_BASIS": st.claim_basis,
                "EFFECTIVE_DATE": st.inception_date,
                "EXPIRY_DATE": st.expiry_date,
                "LIMIT_100": st.limit,
                "ATTACHMENT_POINT_100": st.attachment,
                "CESSION_PCT": st.cession_pct,
                "SIGNED_SHARE_PCT": st.signed_share,
            })

            phys_map = builder_to_physical_map(program.underwriting_department)

            # 2) Conditions rattachées à cette structure (réutilisées via pool)
            for c in st.conditions:
                sig = c.dimension_signature(program.dimension_columns)
                if sig not in pool:
                    cond_id = next_condition_id
                    pool[sig] = cond_id
                    next_condition_id += 1

                    # construire UNE LIGNE condition (dimensions + flags uniquement)
                    row = {
                        "RP_CONDITION_ID": cond_id,
                        "INCLUDES_HULL": c.get("INCLUDES_HULL"),
                        "INCLUDES_LIABILITY": c.get("INCLUDES_LIABILITY"),
                    }
                    for dim in program.dimension_columns:
                        snow_col = phys_map.get(dim, dim)
                        v = c.get_values(dim)
                        row[snow_col] = ';'.join(v) if v else None
                    unique_condition_rows[sig] = row

                cond_id = pool[sig]

                # 3) Field links = overrides financiers (différences condition vs défauts structure)
                _overrides = st.overrides_for(c.to_dict())
                for field_name, new_value in _overrides.items():
                    field_links_rows.append({
                        "RP_CONDITION_ID": cond_id,
                        "RP_STRUCTURE_ID": insper,
                        "FIELD_NAME": field_name,
                        "NEW_VALUE": new_value,
                    })
            insper += 1

        # Émission finale des DataFrames
        conditions_rows = list(unique_condition_rows.values())

        exclusions_df = self._exclusions_to_df(program)
        return {
            "program": program_df,
            "structures": pd.DataFrame(structures_rows),
            "conditions": pd.DataFrame(conditions_rows),
            "exclusions": exclusions_df,
            "field_links": pd.DataFrame(field_links_rows),
        }


    def _exclusions_to_df(self, program: Program) -> pd.DataFrame:
        from .codecs import MULTI_VALUE_SEPARATOR

        prog_dims_builder = list(PROGRAM_TO_BORDEREAU_DIMENSIONS.keys())

        if not program.exclusions:
            cols = ["EXCLUSION_NAME", "EXCL_EFFECTIVE_DATE", "EXCL_EXPIRY_DATE"]
            # colonnes Snowflake
            phys_map = builder_to_physical_map(program.underwriting_department)
            for d in prog_dims_builder:
                cols.append(phys_map.get(d, d))
            return pd.DataFrame(columns=cols)

        rows = []
        for e in program.exclusions:
            row = {
                "EXCLUSION_NAME": e.name,
                "EXCL_EFFECTIVE_DATE": e.effective_date,
                "EXCL_EXPIRY_DATE": e.expiry_date,
            }
            phys_map = builder_to_physical_map(program.underwriting_department)
            for d in prog_dims_builder:
                snow = phys_map.get(d, d)
                vals = e.values_by_dimension.get(d)
                row[snow] = MULTI_VALUE_SEPARATOR.join(vals) if vals else None
            rows.append(row)
        return pd.DataFrame(rows)
