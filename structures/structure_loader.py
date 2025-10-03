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
        program_name = program_row["program_name"]
        
        param_columns = ["structure_name", "cession_PCT", "attachment_point_100", "limit_occurrence_100", "reinsurer_share", "claim_basis", "inception_date", "expiry_date"]
        self.dimension_columns = [col for col in sections_df.columns if col not in param_columns]
        
        program_structures = []
        for _, structure_row in structures_df.iterrows():
            structure_name = structure_row["structure_name"]
            
            structure_sections = sections_df[
                sections_df["structure_name"] == structure_name
            ].to_dict("records")
            
            program_structures.append({
                "structure_name": structure_name,
                "contract_order": structure_row["contract_order"],
                "type_of_participation": structure_row["type_of_participation"],
                "claim_basis": structure_row.get("claim_basis"),
                "inception_date": structure_row.get("inception_date"),
                "expiry_date": structure_row.get("expiry_date"),
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

