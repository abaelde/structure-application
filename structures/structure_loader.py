import pandas as pd
from typing import Dict, Any, List


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
        # Support both old and new data model
        if "REPROG_TITLE" in program_row:
            program_name = program_row["REPROG_TITLE"]
        else:
            program_name = program_row["program_name"]  # Fallback for old format
        
        # Support old, intermediate, and new data models for param columns
        # Old: structure_name, cession_PCT, etc.
        # Intermediate: BUSINESS_TITLE (name-based reference)
        # New: INSPER_ID_PRE (ID-based reference) + all BUSCL_* fields
        param_columns = [
            "structure_name", "BUSINESS_TITLE", "INSPER_ID_PRE",
            "cession_PCT", "CESSION_PCT", "attachment_point_100", "ATTACHMENT_POINT_100",
            "limit_occurrence_100", "LIMIT_OCCURRENCE_100", "reinsurer_share", "SIGNED_SHARE_PCT",
            "claim_basis", "inception_date", "expiry_date",
            "BUSCL_ID_PRE", "REPROG_ID_PRE", "CED_ID_PRE", "BUSINESS_ID_PRE",
            "BUSCL_EXCLUDE_CD", "BUSCL_ENTITY_NAME_CED", "POL_RISK_NAME_CED",
            "BUSCL_COUNTRY_CD", "BUSCL_COUNTRY", "BUSCL_REGION",
            "BUSCL_CLASS_OF_BUSINESS_1", "BUSCL_CLASS_OF_BUSINESS_2", "BUSCL_CLASS_OF_BUSINESS_3",
            "BUSCL_LIMIT_CURRENCY_CD", "AAD_100", "LIMIT_100", "LIMIT_FLOATER_100",
            "OLW_100", "LIMIT_AGG_100", "RETENTION_PCT", "SUPI_100",
            "BUSCL_PREMIUM_CURRENCY_CD", "BUSCL_PREMIUM_GROSS_NET_CD", "PREMIUM_RATE_PCT",
            "PREMIUM_DEPOSIT_100", "PREMIUM_MIN_100", "BUSCL_LIABILITY_1_LINE_100",
            "MAX_COVER_PCT", "MIN_EXCESS_PCT", "AVERAGE_LINE_SLAV_CED",
            "PML_DEFAULT_PCT", "LIMIT_EVENT", "NO_OF_REINSTATEMENTS"
        ]
        self.dimension_columns = [col for col in sections_df.columns if col not in param_columns]
        
        program_structures = []
        for _, structure_row in structures_df.iterrows():
            # Support both old and new data model
            if "BUSINESS_TITLE" in structure_row:
                structure_name = structure_row["BUSINESS_TITLE"]
                structure_id = structure_row.get("INSPER_ID_PRE")
                contract_order = structure_row["INSPER_CONTRACT_ORDER"]
                type_of_participation = structure_row["TYPE_OF_PARTICIPATION_CD"]
                claim_basis = structure_row.get("INSPER_CLAIM_BASIS_CD")
                inception_date = structure_row.get("INSPER_EFFECTIVE_DATE")
                expiry_date = structure_row.get("INSPER_EXPIRY_DATE")
            else:
                structure_name = structure_row["structure_name"]
                structure_id = None
                contract_order = structure_row["contract_order"]
                type_of_participation = structure_row["type_of_participation"]
                claim_basis = structure_row.get("claim_basis")
                inception_date = structure_row.get("inception_date")
                expiry_date = structure_row.get("expiry_date")
            
            # Support old, intermediate, and new data models for sections
            if "INSPER_ID_PRE" in sections_df.columns and structure_id is not None:
                # New model: use INSPER_ID_PRE (ID-based reference)
                structure_sections = sections_df[
                    sections_df["INSPER_ID_PRE"] == structure_id
                ].to_dict("records")
            elif "BUSINESS_TITLE" in sections_df.columns:
                # Intermediate model: use BUSINESS_TITLE (name-based reference)
                structure_sections = sections_df[
                    sections_df["BUSINESS_TITLE"] == structure_name
                ].to_dict("records")
            else:
                # Old model: use structure_name
                structure_sections = sections_df[
                    sections_df["structure_name"] == structure_name
                ].to_dict("records")
            
            program_structures.append({
                "structure_name": structure_name,
                "contract_order": contract_order,
                "type_of_participation": type_of_participation,
                "claim_basis": claim_basis,
                "inception_date": inception_date,
                "expiry_date": expiry_date,
                "sections": structure_sections
            })
        
        program_structures.sort(key=lambda x: x["contract_order"])
        
        self.program = {
            "name": program_name,
            "structures": program_structures,
            "dimension_columns": self.dimension_columns
        }
    
    def get_program(self) -> Dict[str, Any]:
        return self.program

