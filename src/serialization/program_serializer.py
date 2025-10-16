# src/serialization/program_serializer.py
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from src.domain import DIMENSIONS, Program, Structure
from src.domain.constants import PROGRAM_COLS, STRUCTURE_COLS, condition_COLS
from src.domain.dimension_mapping import DIMENSION_COLUMN_MAPPING

MULTI_VALUE_SEPARATOR = ";"


class ProgramSerializer:
    # ---------- Helpers communs ----------
    @staticmethod
    def _to_boolean(value):
        if pd.isna(value):
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            v = value.lower().strip()
            if v in ("true", "1", "yes", "y"):
                return True
            if v in ("false", "0", "no", "n"):
                return False
            return None
        if isinstance(value, (int, float)):
            return bool(value)
        return None

    @staticmethod
    def _split_to_list_strict(cell) -> list[str] | None:
        if pd.isna(cell):
            return None
        tokens = [t.strip() for t in str(cell).split(MULTI_VALUE_SEPARATOR)]
        tokens = [t for t in tokens if t]
        return tokens or None

    @staticmethod
    def _convert_pandas_to_native(value):
        if isinstance(value, list):
            return value
        if pd.isna(value):
            return None
        return value

    @staticmethod
    def _dimension_candidates(conditions_df: pd.DataFrame) -> list[str]:
        program_dims = set(DIMENSIONS) | set(DIMENSION_COLUMN_MAPPING.keys())
        program_dims -= {"INCLUDES_HULL", "INCLUDES_LIABILITY"}  # flags booléens
        return [c for c in program_dims if c in conditions_df.columns]

    # ---------- Import (DFs -> Domain) ----------
    def dataframes_to_program(
        self,
        program_df: pd.DataFrame,
        structures_df: pd.DataFrame,
        conditions_df: pd.DataFrame,
    ) -> Program:

        uw_dept = self._convert_pandas_to_native(
            program_df.iloc[0].get(PROGRAM_COLS.UNDERWRITING_DEPARTMENT)
        )
        name = self._convert_pandas_to_native(program_df.iloc[0][PROGRAM_COLS.TITLE])
        if not uw_dept:
            raise ValueError(
                f"Underwriting department is mandatory for program '{name}'."
            )

        boolean_columns = ["INCLUDES_HULL", "INCLUDES_LIABILITY"]
        for col in boolean_columns:
            if col in conditions_df.columns:
                conditions_df[col] = conditions_df[col].map(
                    self._to_boolean, na_action="ignore"
                )
        if uw_dept and str(uw_dept).lower() == "aviation":
            for col in boolean_columns:
                if col not in conditions_df.columns:
                    raise ValueError(f"Column {col} is required for Aviation programs.")
                nulls = conditions_df[col].isna().sum()
                if nulls > 0:
                    raise ValueError(
                        f"Column {col} has {nulls} null/empty values for Aviation program."
                    )

        dimension_cols = self._dimension_candidates(conditions_df)
        for col in dimension_cols:
            conditions_df[col] = conditions_df[col].map(
                self._split_to_list_strict, na_action="ignore"
            )

        def df_to_dicts(df: pd.DataFrame) -> List[Dict[str, Any]]:
            recs = df.to_dict("records")
            return [
                {k: self._convert_pandas_to_native(v) for k, v in r.items()}
                for r in recs
            ]

        structures_data = df_to_dicts(structures_df)
        conditions_data = df_to_dicts(conditions_df)

        by_struct = {}
        for cond in conditions_data:
            key = cond.get(STRUCTURE_COLS.INSPER_ID)
            if key is None:
                raise ValueError("INSPER_ID_PRE is mandatory for all conditions.")
            by_struct.setdefault(key, []).append(cond)

        structures = []
        for s in structures_data:
            key = s.get(STRUCTURE_COLS.INSPER_ID)
            if key is None:
                raise ValueError("INSPER_ID_PRE is mandatory for all structures.")
            conds = by_struct.get(key, [])
            structures.append(Structure.from_row(s, conds, STRUCTURE_COLS))

        return Program(
            name=name,
            structures=structures,
            dimension_columns=dimension_cols,
            underwriting_department=uw_dept,
        )

    # ---------- Export (Domain -> DFs) ----------
    def program_to_dataframes(self, program: Program) -> Dict[str, pd.DataFrame]:
        reprog_id = 1

        program_df = pd.DataFrame(
            {
                "REPROG_ID_PRE": [reprog_id],
                "REPROG_TITLE": [program.name],
                "CED_ID_PRE": [None],
                "CED_NAME_PRE": [None],
                "REPROG_ACTIVE_IND": [True],
                "REPROG_COMMENT": [None],
                "REPROG_UW_DEPARTMENT_CD": [None],
                "REPROG_UW_DEPARTMENT_NAME": [None],
                "REPROG_UW_DEPARTMENT_LOB_CD": [program.underwriting_department],
                "REPROG_UW_DEPARTMENT_LOB_NAME": [
                    (
                        program.underwriting_department.title()
                        if program.underwriting_department
                        else None
                    )
                ],
                "BUSPAR_CED_REG_CLASS_CD": [None],
                "BUSPAR_CED_REG_CLASS_NAME": [None],
                "REPROG_MAIN_CURRENCY_CD": [None],
                "REPROG_MANAGEMENT_REPORTING_LOB_CD": [None],
            }
        )

        structures_data = {
            "INSPER_ID_PRE": [],
            "BUSINESS_ID_PRE": [],
            "TYPE_OF_PARTICIPATION_CD": [],
            "TYPE_OF_INSURED_PERIOD_CD": [],
            "ACTIVE_FLAG_CD": [],
            "INSPER_EFFECTIVE_DATE": [],
            "INSPER_EXPIRY_DATE": [],
            "REPROG_ID_PRE": [],
            "BUSINESS_TITLE": [],
            "INSPER_LAYER_NO": [],
            "INSPER_MAIN_CURRENCY_CD": [],
            "INSPER_UW_YEAR": [],
            "INSPER_CONTRACT_ORDER": [],
            "INSPER_PREDECESSOR_TITLE": [],
            "INSPER_CONTRACT_FORM_CD_SLAV": [],
            "INSPER_CONTRACT_LODRA_CD_SLAV": [],
            "INSPER_CONTRACT_COVERAGE_CD_SLAV": [],
            "INSPER_CLAIM_BASIS_CD": [],
            "INSPER_LODRA_CD_SLAV": [],
            "INSPER_LOD_TO_RA_DATE_SLAV": [],
            "INSPER_COMMENT": [],
        }

        conditions_data = {
            "BUSCL_ID_PRE": [],
            "REPROG_ID_PRE": [],
            "CED_ID_PRE": [],
            "BUSINESS_ID_PRE": [],
            "INSPER_ID_PRE": [],
            "BUSCL_EXCLUDE_CD": [],
            "BUSCL_ENTITY_NAME_CED": [],
            "POL_RISK_NAME_CED": [],
            "BUSCL_COUNTRY_CD": [],
            "BUSCL_COUNTRY": [],
            "BUSCL_REGION": [],
            "BUSCL_CLASS_OF_BUSINESS_1": [],
            "BUSCL_CLASS_OF_BUSINESS_2": [],
            "BUSCL_CLASS_OF_BUSINESS_3": [],
            "BUSCL_LIMIT_CURRENCY_CD": [],
            "AAD_100": [],
            "LIMIT_100": [],
            "LIMIT_FLOATER_100": [],
            "ATTACHMENT_POINT_100": [],
            "OLW_100": [],
            "LIMIT_AGG_100": [],
            "CESSION_PCT": [],
            "RETENTION_PCT": [],
            "SUPI_100": [],
            "BUSCL_PREMIUM_CURRENCY_CD": [],
            "BUSCL_PREMIUM_GROSS_NET_CD": [],
            "PREMIUM_RATE_PCT": [],
            "PREMIUM_DEPOSIT_100": [],
            "PREMIUM_MIN_100": [],
            "BUSCL_LIABILITY_1_LINE_100": [],
            "MAX_COVER_PCT": [],
            "MIN_EXCESS_PCT": [],
            "SIGNED_SHARE_PCT": [],
            "AVERAGE_LINE_SLAV_CED": [],
            "PML_DEFAULT_PCT": [],
            "LIMIT_EVENT": [],
            "NO_OF_REINSTATEMENTS": [],
            "INCLUDES_HULL": [],
            "INCLUDES_LIABILITY": [],
        }

        def list_to_excel(v):
            if isinstance(v, list):
                return MULTI_VALUE_SEPARATOR.join(map(str, v))
            return v

        insper_id = 1
        buscl_id = 1
        for st in program.structures:
            structures_data["INSPER_ID_PRE"].append(insper_id)
            structures_data["BUSINESS_ID_PRE"].append(None)
            structures_data["TYPE_OF_PARTICIPATION_CD"].append(st.type_of_participation)
            structures_data["TYPE_OF_INSURED_PERIOD_CD"].append(None)
            structures_data["ACTIVE_FLAG_CD"].append(True)
            structures_data["INSPER_EFFECTIVE_DATE"].append(st.inception_date)
            structures_data["INSPER_EXPIRY_DATE"].append(st.expiry_date)
            structures_data["REPROG_ID_PRE"].append(reprog_id)
            structures_data["BUSINESS_TITLE"].append(st.structure_name)
            structures_data["INSPER_LAYER_NO"].append(None)
            structures_data["INSPER_MAIN_CURRENCY_CD"].append(None)
            structures_data["INSPER_UW_YEAR"].append(None)
            structures_data["INSPER_CONTRACT_ORDER"].append(st.contract_order)
            structures_data["INSPER_PREDECESSOR_TITLE"].append(st.predecessor_title)
            structures_data["INSPER_CONTRACT_FORM_CD_SLAV"].append(None)
            structures_data["INSPER_CONTRACT_LODRA_CD_SLAV"].append(None)
            structures_data["INSPER_CONTRACT_COVERAGE_CD_SLAV"].append(None)
            structures_data["INSPER_CLAIM_BASIS_CD"].append(st.claim_basis)
            structures_data["INSPER_LODRA_CD_SLAV"].append(None)
            structures_data["INSPER_LOD_TO_RA_DATE_SLAV"].append(None)
            structures_data["INSPER_COMMENT"].append(None)

            for c in st.conditions:
                d = c.to_dict()

                def g(k):
                    return d.get(k)

                conditions_data["BUSCL_ID_PRE"].append(buscl_id)
                buscl_id += 1
                conditions_data["REPROG_ID_PRE"].append(reprog_id)
                conditions_data["CED_ID_PRE"].append(None)
                conditions_data["BUSINESS_ID_PRE"].append(None)
                conditions_data["INSPER_ID_PRE"].append(insper_id)
                conditions_data["BUSCL_EXCLUDE_CD"].append(g("BUSCL_EXCLUDE_CD"))

                for col in [
                    "BUSCL_ENTITY_NAME_CED",
                    "POL_RISK_NAME_CED",
                    "BUSCL_COUNTRY_CD",
                    "BUSCL_COUNTRY",
                    "BUSCL_REGION",
                    "BUSCL_CLASS_OF_BUSINESS_1",
                    "BUSCL_CLASS_OF_BUSINESS_2",
                    "BUSCL_CLASS_OF_BUSINESS_3",
                    "BUSCL_LIMIT_CURRENCY_CD",
                ]:
                    conditions_data[col].append(list_to_excel(g(col)))

                for col in [
                    "AAD_100",
                    "LIMIT_100",
                    "LIMIT_FLOATER_100",
                    "OLW_100",
                    "LIMIT_AGG_100",
                    "RETENTION_PCT",
                    "SUPI_100",
                    "BUSCL_PREMIUM_CURRENCY_CD",
                    "BUSCL_PREMIUM_GROSS_NET_CD",
                    "PREMIUM_RATE_PCT",
                    "PREMIUM_DEPOSIT_100",
                    "PREMIUM_MIN_100",
                    "BUSCL_LIABILITY_1_LINE_100",
                    "MAX_COVER_PCT",
                    "MIN_EXCESS_PCT",
                    "SIGNED_SHARE_PCT",
                    "AVERAGE_LINE_SLAV_CED",
                    "PML_DEFAULT_PCT",
                    "LIMIT_EVENT",
                    "NO_OF_REINSTATEMENTS",
                    "INCLUDES_HULL",
                    "INCLUDES_LIABILITY",
                ]:
                    conditions_data[col].append(g(col))

                # Gestion spéciale pour les champs avec conversion NaN
                attachment = g(condition_COLS.ATTACHMENT)
                conditions_data["ATTACHMENT_POINT_100"].append(
                    attachment if pd.notna(attachment) else np.nan
                )

                cession = g(condition_COLS.CESSION_PCT)
                conditions_data["CESSION_PCT"].append(
                    cession if pd.notna(cession) else np.nan
                )

            insper_id += 1

        return {
            "program": program_df,
            "structures": pd.DataFrame(structures_data),
            "conditions": pd.DataFrame(conditions_data),
        }
