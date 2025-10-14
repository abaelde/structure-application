import pandas as pd
from typing import Dict, Any, List

from src.domain import (
    DIMENSIONS,
    SHEETS,
    PROGRAM_COLS,
    STRUCTURE_COLS,
    Program,
    Structure,
)


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


def convert_pandas_to_native(value):
    """Convert pandas null values (pd.NA, np.nan) to Python None"""
    if pd.isna(value):
        return None
    return value


def dataframe_to_dict_list(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert DataFrame to list of dicts, replacing pandas nulls with None"""
    records = df.to_dict("records")
    return [
        {key: convert_pandas_to_native(value) for key, value in record.items()}
        for record in records
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

        # Step 3: Convert DataFrames to native Python types
        program_name = convert_pandas_to_native(program_df.iloc[0][PROGRAM_COLS.TITLE])
        program_lob = convert_pandas_to_native(
            program_df.iloc[0].get(PROGRAM_COLS.LINE_OF_BUSINESS)
        )
        structures_data = dataframe_to_dict_list(structures_df)
        sections_data = dataframe_to_dict_list(sections_df)

        # Step 4: Group sections by structure
        sections_by_structure = {}
        for section in sections_data:
            structure_key = section.get(STRUCTURE_COLS.INSPER_ID)
            if structure_key is None:
                structure_key = section.get(STRUCTURE_COLS.NAME)
            
            if structure_key not in sections_by_structure:
                sections_by_structure[structure_key] = []
            sections_by_structure[structure_key].append(section)

        # Step 5: Build Structure objects
        structures = []
        for structure_dict in structures_data:
            structure_key = structure_dict.get(STRUCTURE_COLS.INSPER_ID)
            if structure_key is None:
                structure_key = structure_dict[STRUCTURE_COLS.NAME]
            
            sections_data_for_structure = sections_by_structure.get(structure_key, [])
            structures.append(
                Structure.from_row(structure_dict, sections_data_for_structure, STRUCTURE_COLS)
            )

        # Step 6: Create Program with Structure objects
        self.program = Program(
            name=program_name,
            structures=structures,
            dimension_columns=self.dimension_columns,
            line_of_business=program_lob,
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
