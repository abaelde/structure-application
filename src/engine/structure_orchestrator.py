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
    total_cession_to_layer_100pct = 0.0
    total_cession_to_reinsurer = 0.0
    structures_detail = []

    processed: Set[str] = set()

    def process_structure(structure: Structure) -> None:
        nonlocal total_cession_to_layer_100pct, total_cession_to_reinsurer

        structure_name = structure.structure_name

        if structure_name in processed:
            return

        predecessor_title = structure.predecessor_title

        if pd.notna(predecessor_title):
            predecessor = next(
                (s for s in structures if s.structure_name == predecessor_title), None
            )
            if predecessor:
                process_structure(predecessor)

        matched_section = match_section(
            policy_data, structure.sections, dimension_columns
        )

        if matched_section is None:
            _add_unapplied_structure_detail(
                structures_detail, structure, structure_name, predecessor_title
            )
            structure_outputs[structure_name] = {
                "retained": 0.0,
                "cession_to_layer_100pct": 0.0,
                "cession_to_reinsurer": 0.0,
                "type_of_participation": structure.type_of_participation,
                "retention_pct": 1.0,
            }
            processed.add(structure_name)
            return

        input_exposure = _calculate_input_exposure(
            exposure, predecessor_title, structure_outputs
        )

        section_to_apply, rescaling_info = _rescale_section_if_needed(
            matched_section, predecessor_title, structure, structure_outputs
        )

        ceded_result = apply_section(
            input_exposure, section_to_apply, structure.type_of_participation
        )

        retained = input_exposure - ceded_result["cession_to_layer_100pct"]

        current_retention_pct = _calculate_retention_pct(
            structure.type_of_participation, matched_section
        )

        structure_outputs[structure_name] = {
            "retained": retained,
            "cession_to_layer_100pct": ceded_result["cession_to_layer_100pct"],
            "cession_to_reinsurer": ceded_result["cession_to_reinsurer"],
            "type_of_participation": structure.type_of_participation,
            "retention_pct": current_retention_pct,
        }

        _add_applied_structure_detail(
            structures_detail,
            structure,
            structure_name,
            predecessor_title,
            input_exposure,
            ceded_result,
            matched_section,
            section_to_apply,
            rescaling_info,
        )

        processed.add(structure_name)

    for structure in structures:
        process_structure(structure)

    for detail in structures_detail:
        if detail["applied"]:
            total_cession_to_layer_100pct += detail["cession_to_layer_100pct"]
            total_cession_to_reinsurer += detail["cession_to_reinsurer"]

    return structures_detail, total_cession_to_layer_100pct, total_cession_to_reinsurer


def _calculate_input_exposure(
    base_exposure: float,
    predecessor_title: Optional[str],
    structure_outputs: Dict[str, Dict[str, Any]],
) -> float:
    if pd.notna(predecessor_title) and predecessor_title in structure_outputs:
        return structure_outputs[predecessor_title]["retained"]
    return base_exposure


def _rescale_section_if_needed(
    matched_section: Section,
    predecessor_title: Optional[str],
    structure: Structure,
    structure_outputs: Dict[str, Dict[str, Any]],
) -> tuple[Section, Optional[Dict[str, Any]]]:
    section_to_apply = matched_section.copy()
    rescaling_info = None

    if pd.notna(predecessor_title) and predecessor_title in structure_outputs:
        predecessor_info = structure_outputs[predecessor_title]
        predecessor_type = predecessor_info.get("type_of_participation")
        current_type = structure.type_of_participation

        if (
            predecessor_type == PRODUCT.QUOTA_SHARE
            and current_type == PRODUCT.EXCESS_OF_LOSS
        ):
            retention_factor = predecessor_info.get("retention_pct", 1.0)

            original_attachment = None
            original_limit = None
            rescaled_attachment = None
            rescaled_limit = None

            if SC.ATTACHMENT in section_to_apply and pd.notna(
                section_to_apply[SC.ATTACHMENT]
            ):
                original_attachment = section_to_apply[SC.ATTACHMENT]
                section_to_apply[SC.ATTACHMENT] = (
                    section_to_apply[SC.ATTACHMENT] * retention_factor
                )
                rescaled_attachment = section_to_apply[SC.ATTACHMENT]

            if SC.LIMIT in section_to_apply and pd.notna(section_to_apply[SC.LIMIT]):
                original_limit = section_to_apply[SC.LIMIT]
                section_to_apply[SC.LIMIT] = (
                    section_to_apply[SC.LIMIT] * retention_factor
                )
                rescaled_limit = section_to_apply[SC.LIMIT]

            rescaling_info = {
                "retention_factor": retention_factor,
                "original_attachment": original_attachment,
                "rescaled_attachment": rescaled_attachment,
                "original_limit": original_limit,
                "rescaled_limit": rescaled_limit,
            }

    return section_to_apply, rescaling_info


def _calculate_retention_pct(
    type_of_participation: str, matched_section: Section
) -> float:
    if type_of_participation == PRODUCT.QUOTA_SHARE:
        cession_pct = matched_section.get(SC.CESSION_PCT, 0.0)
        if pd.notna(cession_pct):
            return 1.0 - cession_pct
    return 1.0


def _add_unapplied_structure_detail(
    structures_detail: List[Dict[str, Any]],
    structure: Structure,
    structure_name: str,
    predecessor_title: Optional[str],
) -> None:
    structures_detail.append(
        {
            "structure_name": structure_name,
            "type_of_participation": structure.type_of_participation,
            "claim_basis": structure.claim_basis,
            "inception_date": structure.inception_date,
            "expiry_date": structure.expiry_date,
            "input_exposure": 0.0,
            "cession_to_layer_100pct": 0.0,
            "cession_to_reinsurer": 0.0,
            "reinsurer_share": 0.0,
            "applied": False,
            "section": None,
            "predecessor_title": (
                predecessor_title if pd.notna(predecessor_title) else None
            ),
        }
    )


def _add_applied_structure_detail(
    structures_detail: List[Dict[str, Any]],
    structure: Structure,
    structure_name: str,
    predecessor_title: Optional[str],
    input_exposure: float,
    ceded_result: Dict[str, float],
    matched_section: Section,
    section_to_apply: Section,
    rescaling_info: Optional[Dict[str, Any]],
) -> None:
    structures_detail.append(
        {
            "structure_name": structure_name,
            "type_of_participation": structure.type_of_participation,
            "claim_basis": structure.claim_basis,
            "inception_date": structure.inception_date,
            "expiry_date": structure.expiry_date,
            "input_exposure": input_exposure,
            "cession_to_layer_100pct": ceded_result["cession_to_layer_100pct"],
            "cession_to_reinsurer": ceded_result["cession_to_reinsurer"],
            "reinsurer_share": ceded_result["reinsurer_share"],
            "applied": True,
            "section": matched_section,
            "section_rescaled": section_to_apply,
            "predecessor_title": (
                predecessor_title if pd.notna(predecessor_title) else None
            ),
            "rescaling_info": rescaling_info,
        }
    )
