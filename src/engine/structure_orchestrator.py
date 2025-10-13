import pandas as pd
from typing import Dict, Any, List, Set, Optional
from src.domain import PRODUCT, SECTION_COLS as SC, Structure, Section
from .section_matcher import match_section
from .cession_calculator import apply_section


def process_structures(
    structures: List[Structure],
    policy_data: Dict[str, Any],
    dimension_columns: List[str],
    exposure: float,
) -> tuple[List[Dict[str, Any]], float, float]:
    structure_outputs = {}
    structures_detail = []
    processed: Set[str] = set()

    def process_structure(structure: Structure) -> Dict[str, Any]:
        if _is_already_processed(structure.structure_name):
            return _no_cession_result()

        _process_predecessor_if_needed(structure)

        matched_section = match_section(
            policy_data, structure.sections, dimension_columns
        )

        if matched_section is None:
            return _handle_no_matching_section(structure)

        return _apply_structure_and_calculate_cession(structure, matched_section)

    def _is_already_processed(structure_name: str) -> bool:
        return structure_name in processed

    def _no_cession_result() -> Dict[str, Any]:
        return {"applied": False, "cession_to_layer_100pct": 0.0, "cession_to_reinsurer": 0.0}

    def _process_predecessor_if_needed(structure: Structure) -> None:
        if not structure.has_predecessor():
            return

        predecessor = next(
            (s for s in structures if s.structure_name == structure.predecessor_title), None
        )
        if predecessor:
            process_structure(predecessor)

    def _handle_no_matching_section(structure: Structure) -> Dict[str, Any]:
        _add_structure_detail(structures_detail, structure, applied=False)
        structure_outputs[structure.structure_name] = {
            "retained": 0.0,
            "cession_to_layer_100pct": 0.0,
            "cession_to_reinsurer": 0.0,
            "type_of_participation": structure.type_of_participation,
            "retention_pct": 1.0,
        }
        processed.add(structure.structure_name)
        return _no_cession_result()

    def _apply_structure_and_calculate_cession(
        structure: Structure, matched_section: Section
    ) -> Dict[str, Any]:
        input_exposure = _calculate_input_exposure(exposure, structure, structure_outputs)
        
        section_to_apply, rescaling_info = _rescale_section_if_needed(
            matched_section, structure, structure_outputs
        )

        ceded_result = apply_section(
            input_exposure, section_to_apply, structure.type_of_participation
        )

        retained = input_exposure - ceded_result["cession_to_layer_100pct"]
        current_retention_pct = _calculate_retention_pct(structure, matched_section)

        structure_outputs[structure.structure_name] = {
            "retained": retained,
            "cession_to_layer_100pct": ceded_result["cession_to_layer_100pct"],
            "cession_to_reinsurer": ceded_result["cession_to_reinsurer"],
            "type_of_participation": structure.type_of_participation,
            "retention_pct": current_retention_pct,
        }

        _add_structure_detail(
            structures_detail,
            structure,
            applied=True,
            input_exposure=input_exposure,
            ceded_result=ceded_result,
            matched_section=matched_section,
            section_to_apply=section_to_apply,
            rescaling_info=rescaling_info,
        )

        processed.add(structure.structure_name)
        
        return {
            "applied": True,
            "cession_to_layer_100pct": ceded_result["cession_to_layer_100pct"],
            "cession_to_reinsurer": ceded_result["cession_to_reinsurer"]
        }

    total_cession_to_layer_100pct = 0.0
    total_cession_to_reinsurer = 0.0

    for structure in structures:
        result = process_structure(structure)
        if result["applied"]:
            total_cession_to_layer_100pct += result["cession_to_layer_100pct"]
            total_cession_to_reinsurer += result["cession_to_reinsurer"]

    return structures_detail, total_cession_to_layer_100pct, total_cession_to_reinsurer


def _calculate_input_exposure(
    base_exposure: float,
    structure: Structure,
    structure_outputs: Dict[str, Dict[str, Any]],
) -> float:
    if structure.has_predecessor() and structure.predecessor_title in structure_outputs:
        return structure_outputs[structure.predecessor_title]["retained"]
    return base_exposure


def _rescale_section_if_needed(
    matched_section: Section,
    structure: Structure,
    structure_outputs: Dict[str, Dict[str, Any]],
) -> tuple[Section, Optional[Dict[str, Any]]]:
    if not structure.has_predecessor() or structure.predecessor_title not in structure_outputs:
        return matched_section.copy(), None

    predecessor_info = structure_outputs[structure.predecessor_title]
    predecessor_type = predecessor_info.get("type_of_participation")

    if predecessor_type == PRODUCT.QUOTA_SHARE and structure.is_excess_of_loss():
        retention_factor = predecessor_info.get("retention_pct", 1.0)
        return matched_section.rescale_for_predecessor(retention_factor)

    return matched_section.copy(), None


def _calculate_retention_pct(structure: Structure, matched_section: Section) -> float:
    return structure.calculate_retention_pct(matched_section)


def _add_structure_detail(
    structures_detail: List[Dict[str, Any]],
    structure: Structure,
    applied: bool,
    input_exposure: float = 0.0,
    ceded_result: Optional[Dict[str, float]] = None,
    matched_section: Optional[Section] = None,
    section_to_apply: Optional[Section] = None,
    rescaling_info: Optional[Dict[str, Any]] = None,
) -> None:
    detail = {
        "structure_name": structure.structure_name,
        "type_of_participation": structure.type_of_participation,
        "claim_basis": structure.claim_basis,
        "inception_date": structure.inception_date,
        "expiry_date": structure.expiry_date,
        "input_exposure": input_exposure,
        "applied": applied,
        "predecessor_title": structure.predecessor_title if structure.has_predecessor() else None,
    }

    if applied and ceded_result:
        detail.update({
            "cession_to_layer_100pct": ceded_result["cession_to_layer_100pct"],
            "cession_to_reinsurer": ceded_result["cession_to_reinsurer"],
            "reinsurer_share": ceded_result["reinsurer_share"],
            "section": matched_section,
            "section_rescaled": section_to_apply,
            "rescaling_info": rescaling_info,
        })
    else:
        detail.update({
            "cession_to_layer_100pct": 0.0,
            "cession_to_reinsurer": 0.0,
            "reinsurer_share": 0.0,
            "section": None,
        })

    structures_detail.append(detail)
