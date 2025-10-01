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
        
        param_columns = ["structure_name", "session_rate", "priority", "limit"]
        self.dimension_columns = [col for col in sections_df.columns if col not in param_columns]
        
        program_structures = []
        for _, structure_row in structures_df.iterrows():
            structure_name = structure_row["structure_name"]
            
            structure_sections = sections_df[
                sections_df["structure_name"] == structure_name
            ].to_dict("records")
            
            program_structures.append({
                "structure_name": structure_name,
                "order": structure_row["order"],
                "product_type": structure_row["product_type"],
                "sections": structure_sections
            })
        
        program_structures.sort(key=lambda x: x["order"])
        
        self.program = {
            "name": program_name,
            "mode": program_row["mode"],
            "structures": program_structures,
            "dimension_columns": self.dimension_columns
        }
    
    def get_program(self) -> Dict[str, Any]:
        return self.program

