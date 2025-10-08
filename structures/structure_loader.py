import pandas as pd
from typing import Dict, Any, List

from .constants import DIMENSIONS, SHEETS, PROGRAM_COLS, STRUCTURE_COLS


# Keys and relations - foreign keys between Excel sheets (tables)
KEYS_AND_RELATIONS = [
    "REPROG_ID_PRE",  # Program identifier
    "INSPER_ID_PRE",  # Structure identifier (links structures to sections)
    "BUSCL_ID_PRE",  # Business class identifier
    "CED_ID_PRE",  # Cedant identifier (not used)
    "BUSINESS_ID_PRE",  # Business identifier (not used)
    "BUSINESS_TITLE",  # Structure name (used for matching when INSPER_ID_PRE is null)
]

# Parameters - used in reinsurance calculations and structure configuration
PARAMETERS = [
    # Structure configuration parameters
    "TYPE_OF_PARTICIPATION_CD",  # Defines structure type (quota_share, excess_of_loss)
    "INSPER_CONTRACT_ORDER",  # Defines application order of structures
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


class ProgramLoader:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.program = None
        self.dimension_columns = []
        self.load_program()

    def load_program(self):
        program_df = pd.read_excel(self.excel_path, sheet_name=SHEETS.PROGRAM)
        structures_df = pd.read_excel(self.excel_path, sheet_name=SHEETS.STRUCTURES)
        sections_df = pd.read_excel(self.excel_path, sheet_name=SHEETS.SECTIONS)

        program_row = program_df.iloc[0]
        program_name = program_row[PROGRAM_COLS.TITLE]

        # Use only explicitly defined dimensions that exist in sections_df
        self.dimension_columns = [
            col for col in DIMENSIONS if col in sections_df.columns
        ]

        program_structures = []
        for _, structure_row in structures_df.iterrows():
            structure_name = structure_row[STRUCTURE_COLS.NAME]
            structure_id = structure_row.get(STRUCTURE_COLS.INSPER_ID)
            contract_order = structure_row[STRUCTURE_COLS.ORDER]
            type_of_participation = structure_row[STRUCTURE_COLS.TYPE]
            claim_basis = structure_row.get(STRUCTURE_COLS.CLAIM_BASIS)
            inception_date = structure_row.get(STRUCTURE_COLS.INCEPTION)
            expiry_date = structure_row.get(STRUCTURE_COLS.EXPIRY)

            if structure_id is not None:
                structure_sections = sections_df[
                    sections_df[STRUCTURE_COLS.INSPER_ID] == structure_id
                ].to_dict("records")
            else:
                structure_sections = sections_df[
                    sections_df[STRUCTURE_COLS.NAME] == structure_name
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
