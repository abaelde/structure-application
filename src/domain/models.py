from typing import Dict, Any, List, Optional
import pandas as pd
from .constants import SECTION_COLS


class Section:
    def __init__(self, data: Dict[str, Any]):
        self._data = data.copy()
        self.cession_pct = data.get(SECTION_COLS.CESSION_PCT)
        self.attachment = data.get(SECTION_COLS.ATTACHMENT)
        self.limit = data.get(SECTION_COLS.LIMIT)
        self.signed_share = data.get(SECTION_COLS.SIGNED_SHARE)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Section':
        """Factory method: create Section from dictionary"""
        return cls(data)
    
    def get(self, key: str, default=None):
        return self._data.get(key, default)
    
    def __getitem__(self, key: str):
        return self._data[key]
    
    def __setitem__(self, key: str, value: Any):
        self._data[key] = value
        if key == SECTION_COLS.CESSION_PCT:
            self.cession_pct = value
        elif key == SECTION_COLS.ATTACHMENT:
            self.attachment = value
        elif key == SECTION_COLS.LIMIT:
            self.limit = value
        elif key == SECTION_COLS.SIGNED_SHARE:
            self.signed_share = value
    
    def __contains__(self, key: str) -> bool:
        return key in self._data
    
    def copy(self) -> 'Section':
        return Section(self._data.copy())
    
    def to_dict(self) -> Dict[str, Any]:
        return self._data.copy()


class Structure:
    def __init__(
        self,
        structure_name: str,
        contract_order: int,
        type_of_participation: str,
        sections: List['Section'],
        predecessor_title: Optional[str] = None,
        claim_basis: Optional[str] = None,
        inception_date: Optional[str] = None,
        expiry_date: Optional[str] = None,
    ):
        self.structure_name = structure_name
        self.contract_order = contract_order
        self.type_of_participation = type_of_participation
        self.predecessor_title = predecessor_title
        self.claim_basis = claim_basis
        self.inception_date = inception_date
        self.expiry_date = expiry_date
        self.sections = sections
    
    @classmethod
    def from_row(
        cls,
        structure_row: pd.Series,
        sections_df: pd.DataFrame,
        structure_cols,
    ) -> 'Structure':
        """
        Factory method: create Structure from DataFrame row.
        The Structure knows how to find and link its own sections.
        """
        structure_name = structure_row[structure_cols.NAME]
        structure_id = structure_row.get(structure_cols.INSPER_ID)
        
        # Logic to filter sections belongs to the Structure class
        if pd.notna(structure_id):
            sections_data = sections_df[
                sections_df[structure_cols.INSPER_ID] == structure_id
            ].to_dict("records")
        else:
            sections_data = sections_df[
                sections_df[structure_cols.NAME] == structure_name
            ].to_dict("records")
        
        # Create Section objects
        sections = [Section.from_dict(s) for s in sections_data]
        
        # Create and return Structure
        return cls(
            structure_name=structure_name,
            contract_order=structure_row[structure_cols.ORDER],
            type_of_participation=structure_row[structure_cols.TYPE],
            sections=sections,
            predecessor_title=structure_row.get(structure_cols.PREDECESSOR),
            claim_basis=structure_row.get(structure_cols.CLAIM_BASIS),
            inception_date=structure_row.get(structure_cols.INCEPTION),
            expiry_date=structure_row.get(structure_cols.EXPIRY),
        )
    
    def get(self, key: str, default=None):
        return getattr(self, key, default)
    
    def __getitem__(self, key: str):
        if not hasattr(self, key):
            raise KeyError(f"'{key}' not found in Structure")
        return getattr(self, key)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "structure_name": self.structure_name,
            "contract_order": self.contract_order,
            "type_of_participation": self.type_of_participation,
            "predecessor_title": self.predecessor_title,
            "claim_basis": self.claim_basis,
            "inception_date": self.inception_date,
            "expiry_date": self.expiry_date,
            "sections": [s.to_dict() for s in self.sections],
        }


class Program:
    def __init__(
        self,
        name: str,
        structures: List[Structure],
        dimension_columns: List[str],
    ):
        self.name = name
        self.dimension_columns = dimension_columns
        self.structures = structures
    
    @classmethod
    def from_dataframes(
        cls,
        program_df: pd.DataFrame,
        structures_df: pd.DataFrame,
        sections_df: pd.DataFrame,
        program_cols,
        structure_cols,
        dimension_columns: List[str],
    ) -> 'Program':
        """
        Factory method: create Program from DataFrames.
        The Program orchestrates its own construction.
        """
        program_name = program_df.iloc[0][program_cols.TITLE]
        
        # Create all structures (they know how to build themselves)
        structures = [
            Structure.from_row(row, sections_df, structure_cols)
            for _, row in structures_df.iterrows()
        ]
        
        return cls(
            name=program_name,
            structures=structures,
            dimension_columns=dimension_columns,
        )
    
    def __getitem__(self, key: str):
        if not hasattr(self, key):
            raise KeyError(f"'{key}' not found in Program")
        return getattr(self, key)
    
    @property
    def all_sections(self) -> List[Section]:
        """Returns all sections from all structures"""
        sections = []
        for structure in self.structures:
            sections.extend(structure.sections)
        return sections
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "structures": [s.to_dict() for s in self.structures],
            "dimension_columns": self.dimension_columns,
        }

