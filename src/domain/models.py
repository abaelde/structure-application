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
        sections: List[Dict[str, Any]],
        **kwargs
    ):
        self.structure_name = structure_name
        self.contract_order = contract_order
        self.type_of_participation = type_of_participation
        self.predecessor_title = kwargs.get("predecessor_title")
        self.claim_basis = kwargs.get("claim_basis")
        self.inception_date = kwargs.get("inception_date")
        self.expiry_date = kwargs.get("expiry_date")
        self.sections = [Section(s) if isinstance(s, dict) else s for s in sections]
    
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
            "sections": [s.to_dict() if isinstance(s, Section) else s for s in self.sections],
        }


class Program:
    def __init__(
        self,
        name: str,
        structures: List[Dict[str, Any]],
        dimension_columns: List[str],
    ):
        self.name = name
        self.dimension_columns = dimension_columns
        self.structures = [
            Structure(**s) if isinstance(s, dict) else s for s in structures
        ]
    
    def __getitem__(self, key: str):
        if not hasattr(self, key):
            raise KeyError(f"'{key}' not found in Program")
        return getattr(self, key)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "structures": [s.to_dict() if isinstance(s, Structure) else s for s in self.structures],
            "dimension_columns": self.dimension_columns,
        }

