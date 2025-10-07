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
        
        # Support both old and new data model for param columns
        param_columns = ["structure_name", "BUSINESS_TITLE", "cession_PCT", "attachment_point_100", "limit_occurrence_100", "reinsurer_share", "claim_basis", "inception_date", "expiry_date"]
        self.dimension_columns = [col for col in sections_df.columns if col not in param_columns]
        
        program_structures = []
        for _, structure_row in structures_df.iterrows():
            # Support both old and new data model
            if "BUSINESS_TITLE" in structure_row:
                structure_name = structure_row["BUSINESS_TITLE"]
                contract_order = structure_row["INSPER_CONTRACT_ORDER"]
                type_of_participation = structure_row["TYPE_OF_PARTICIPATION_CD"]
                claim_basis = structure_row.get("INSPER_CLAIM_BASIS_CD")
                inception_date = structure_row.get("INSPER_EFFECTIVE_DATE")
                expiry_date = structure_row.get("INSPER_EXPIRY_DATE")
            else:
                structure_name = structure_row["structure_name"]
                contract_order = structure_row["contract_order"]
                type_of_participation = structure_row["type_of_participation"]
                claim_basis = structure_row.get("claim_basis")
                inception_date = structure_row.get("inception_date")
                expiry_date = structure_row.get("expiry_date")
            
            # Support both old and new data model for sections
            if "BUSINESS_TITLE" in sections_df.columns:
                structure_sections = sections_df[
                    sections_df["BUSINESS_TITLE"] == structure_name
                ].to_dict("records")
            else:
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

