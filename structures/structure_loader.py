import pandas as pd
from typing import Dict, Any


class ProgramLoader:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.program = None
        self.load_program()
    
    def load_program(self):
        program_df = pd.read_excel(self.excel_path, sheet_name="program")
        structures_df = pd.read_excel(self.excel_path, sheet_name="structures")
        conditions_df = pd.read_excel(self.excel_path, sheet_name="conditions")
        
        program_row = program_df.iloc[0]
        program_name = program_row["program_name"]
        
        program_structures = []
        for _, structure_row in structures_df.iterrows():
            structure_name = structure_row["structure_name"]
            
            structure_conditions = conditions_df[
                conditions_df["structure_name"] == structure_name
            ].to_dict("records")
            
            program_structures.append({
                "structure_name": structure_name,
                "order": structure_row["order"],
                "product_type": structure_row["product_type"],
                "session_rate": structure_row.get("session_rate"),
                "priority": structure_row.get("priority"),
                "limit": structure_row.get("limit"),
                "conditions": structure_conditions
            })
        
        program_structures.sort(key=lambda x: x["order"])
        
        self.program = {
            "name": program_name,
            "mode": program_row["mode"],
            "structures": program_structures
        }
    
    def get_program(self) -> Dict[str, Any]:
        return self.program

