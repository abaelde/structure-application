import pandas as pd
from typing import Dict, Any, List


# Keys and relations - necessary for program structure
KEYS_AND_RELATIONS = [
    "BUSCL_ID_PRE",
    "REPROG_ID_PRE",
    "CED_ID_PRE",
    "BUSINESS_ID_PRE",
    "INSPER_ID_PRE",
    "BUSINESS_TITLE",
    "TYPE_OF_PARTICIPATION_CD",
    "INSPER_CONTRACT_ORDER",
]

# Parameters - used in reinsurance calculations
PARAMETERS = [
    # Core calculation parameters
    "CESSION_PCT",
    "ATTACHMENT_POINT_100",
    "LIMIT_OCCURRENCE_100",
    "SIGNED_SHARE_PCT",
    # Claim basis parameters
    "INSPER_CLAIM_BASIS_CD",
    "INSPER_EFFECTIVE_DATE",
    "INSPER_EXPIRY_DATE",
    # Advanced limit parameters
    "AAD_100",
    "LIMIT_100",
    "LIMIT_FLOATER_100",
    "OLW_100",
    "LIMIT_AGG_100",
    "RETENTION_PCT",
    "SUPI_100",
    # Premium parameters
    "BUSCL_PREMIUM_CURRENCY_CD",
    "BUSCL_PREMIUM_GROSS_NET_CD",
    "PREMIUM_RATE_PCT",
    "PREMIUM_DEPOSIT_100",
    "PREMIUM_MIN_100",
    # Coverage parameters
    "BUSCL_LIABILITY_1_LINE_100",
    "MAX_COVER_PCT",
    "MIN_EXCESS_PCT",
    "AVERAGE_LINE_SLAV_CED",
    "PML_DEFAULT_PCT",
    "LIMIT_EVENT",
    "NO_OF_REINSTATEMENTS",
    # Currency parameters
    "REPROG_MAIN_CURRENCY_CD",
    "INSPER_MAIN_CURRENCY_CD",
]

# Dimensions are automatically derived: any column not in KEYS_AND_RELATIONS or PARAMETERS
# Expected dimensions:
#   - BUSCL_COUNTRY_CD, BUSCL_REGION
#   - BUSCL_CLASS_OF_BUSINESS_1, BUSCL_CLASS_OF_BUSINESS_2, BUSCL_CLASS_OF_BUSINESS_3
#   - BUSCL_LIMIT_CURRENCY_CD
#   - BUSCL_EXCLUDE_CD, BUSCL_ENTITY_NAME_CED, POL_RISK_NAME_CED


class ProgramLoader:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.program = None
        self.dimension_columns = []
        self.load_program()

    def load_program(self):
        program_df = pd.read_excel(self.excel_path, sheet_name="program")
        structures_df = pd.read_excel(self.excel_path, sheet_name="structures")
        sections_df = pd.read_excel(self.excel_path, sheet_name="sections")

        program_row = program_df.iloc[0]
        program_name = program_row["REPROG_TITLE"]

        # Dimensions are derived: all columns except keys/relations and parameters
        non_dimension_columns = KEYS_AND_RELATIONS + PARAMETERS
        self.dimension_columns = [
            col for col in sections_df.columns if col not in non_dimension_columns
        ]

        program_structures = []
        for _, structure_row in structures_df.iterrows():
            structure_name = structure_row["BUSINESS_TITLE"]
            structure_id = structure_row.get("INSPER_ID_PRE")
            contract_order = structure_row["INSPER_CONTRACT_ORDER"]
            type_of_participation = structure_row["TYPE_OF_PARTICIPATION_CD"]
            claim_basis = structure_row.get("INSPER_CLAIM_BASIS_CD")
            inception_date = structure_row.get("INSPER_EFFECTIVE_DATE")
            expiry_date = structure_row.get("INSPER_EXPIRY_DATE")

            if structure_id is not None:
                structure_sections = sections_df[
                    sections_df["INSPER_ID_PRE"] == structure_id
                ].to_dict("records")
            else:
                structure_sections = sections_df[
                    sections_df["BUSINESS_TITLE"] == structure_name
                ].to_dict("records")

            program_structures.append(
                {
                    "structure_name": structure_name,
                    "contract_order": contract_order,
                    "type_of_participation": type_of_participation,
                    "claim_basis": claim_basis,
                    "inception_date": inception_date,
                    "expiry_date": expiry_date,
                    "sections": structure_sections,
                }
            )

        program_structures.sort(key=lambda x: x["contract_order"])

        self.program = {
            "name": program_name,
            "structures": program_structures,
            "dimension_columns": self.dimension_columns,
        }

    def get_program(self) -> Dict[str, Any]:
        return self.program
