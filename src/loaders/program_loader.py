import pandas as pd
from typing import Dict, Any, List

from src.domain import DIMENSIONS, SHEETS, PROGRAM_COLS, STRUCTURE_COLS, Program, Structure, Section


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
    "INSPER_CONTRACT_ORDER",  # Defines application order of structures (deprecated)
    "INSPER_PREDECESSOR_TITLE",  # Inuring mechanism: name of predecessor structure
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
    def __init__(self, source: str, data_source: str = "file"):
        self.source = source
        self.data_source = data_source
        self.program = None
        self.dimension_columns = []
        self.load_program()

    def load_program(self):
        # Step 1: Load data from source (only responsibility of the loader)
        if self.data_source == "file":
            program_df, structures_df, sections_df = self._load_from_file()
        elif self.data_source == "snowflake":
            program_df, structures_df, sections_df = self._load_from_snowflake()
        else:
            raise ValueError(f"Unknown data_source: {self.data_source}")

        # Step 2: Determine dimension columns
        self.dimension_columns = [
            col for col in DIMENSIONS if col in sections_df.columns
        ]

        # Step 3: Let the Program build itself from the DataFrames
        # The construction logic is delegated to the domain models
        self.program = Program.from_dataframes(
            program_df=program_df,
            structures_df=structures_df,
            sections_df=sections_df,
            program_cols=PROGRAM_COLS,
            structure_cols=STRUCTURE_COLS,
            dimension_columns=self.dimension_columns,
        )

    def _load_from_file(self):
        program_df = pd.read_excel(self.source, sheet_name=SHEETS.PROGRAM)
        structures_df = pd.read_excel(self.source, sheet_name=SHEETS.STRUCTURES)
        sections_df = pd.read_excel(self.source, sheet_name=SHEETS.SECTIONS)
        return program_df, structures_df, sections_df
    
    def _load_from_snowflake(self):
        raise NotImplementedError("Snowflake loading not yet implemented")

    def get_program(self) -> Program:
        return self.program

