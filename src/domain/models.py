from typing import Dict, Any, List, Optional
from .constants import SECTION_COLS, PRODUCT


class Section:
    def __init__(self, data: Dict[str, Any]):
        self._data = data.copy()
        self.cession_pct = data.get(SECTION_COLS.CESSION_PCT)
        self.attachment = data.get(SECTION_COLS.ATTACHMENT)
        self.limit = data.get(SECTION_COLS.LIMIT)
        self.signed_share = data.get(SECTION_COLS.SIGNED_SHARE)
        self._validate()

    def _validate(self):
        
        # Les sections d'exclusion n'ont pas besoin de SIGNED_SHARE_PCT
        is_exclusion = self._data.get("BUSCL_EXCLUDE_CD") == "exclude"
        if is_exclusion:
            return
        
        if self.signed_share is None:
            raise ValueError(
                f"SIGNED_SHARE_PCT is required for all non-exclusion sections. "
                f"Section data: {self._data}"
            )
        if not 0 <= self.signed_share <= 1:
            raise ValueError(
                f"SIGNED_SHARE_PCT must be between 0 and 1, got {self.signed_share}"
            )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Section":
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

    def copy(self) -> "Section":
        return Section(self._data.copy())

    def to_dict(self) -> Dict[str, Any]:
        return self._data.copy()

    def has_attachment(self) -> bool:
        return self.attachment is not None

    def has_limit(self) -> bool:
        return self.limit is not None

    def has_cession_pct(self) -> bool:
        return self.cession_pct is not None

    def is_exclusion(self) -> bool:
        return self.get("BUSCL_EXCLUDE_CD") == "exclude"

    def rescale_for_predecessor(self, retention_factor: float) -> tuple["Section", Dict[str, Any]]:
        rescaled_section = self.copy()
        rescaling_info = {
            "retention_factor": retention_factor,
            "original_attachment": None,
            "rescaled_attachment": None,
            "original_limit": None,
            "rescaled_limit": None,
        }

        if self.has_attachment():
            rescaling_info["original_attachment"] = self.attachment
            rescaled_section[SECTION_COLS.ATTACHMENT] = self.attachment * retention_factor
            rescaling_info["rescaled_attachment"] = rescaled_section.attachment

        if self.has_limit():
            rescaling_info["original_limit"] = self.limit
            rescaled_section[SECTION_COLS.LIMIT] = self.limit * retention_factor
            rescaling_info["rescaled_limit"] = rescaled_section.limit

        return rescaled_section, rescaling_info


class Structure:
    def __init__(
        self,
        structure_name: str,
        contract_order: int,
        type_of_participation: str,
        sections: List["Section"],
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
        structure_row: Dict[str, Any],
        sections_data: List[Dict[str, Any]],
        structure_cols,
    ) -> "Structure":
        """
        Factory method: create Structure from dictionary data.
        The Structure knows how to find and link its own sections.
        """
        # Create Section objects
        sections = [Section.from_dict(s) for s in sections_data]

        # Create and return Structure
        return cls(
            structure_name=structure_row[structure_cols.NAME],
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

    def has_predecessor(self) -> bool:
        return self.predecessor_title is not None

    def is_quota_share(self) -> bool:
        
        return self.type_of_participation == PRODUCT.QUOTA_SHARE

    def is_excess_of_loss(self) -> bool:
        return self.type_of_participation == PRODUCT.EXCESS_OF_LOSS

    def calculate_retention_pct(self, matched_section: Section) -> float:
        if self.is_quota_share() and matched_section.has_cession_pct():
            return 1.0 - matched_section.cession_pct
        return 1.0


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
