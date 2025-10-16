from typing import Dict, Any, List, Set, Optional
from src.domain import PRODUCT, Structure, Condition
from src.domain.policy import Policy
from .condition_matcher import match_condition
from .cession_calculator import apply_condition
from src.domain.exposure_components import ExposureComponents


def process_structures(
    structures: List[Structure],
    policy: Policy,
    dimension_columns: List[str],
    exposure: float,
    line_of_business: str = None,
) -> tuple[List[Dict[str, Any]], float, float]:
    structure_outputs = {}
    structures_detail = []
    processed: Set[str] = set()

    def process_structure(structure: Structure) -> Dict[str, Any]:
        if _is_already_processed(structure.structure_name):
            return _no_cession_result()

        _process_predecessor_if_needed(structure)

        matched_condition = match_condition(
            policy, structure.conditions, dimension_columns
        )

        if matched_condition is None:
            return _handle_no_matching_condition(structure)

        return _apply_structure_and_calculate_cession(structure, matched_condition)

    def _is_already_processed(structure_name: str) -> bool:
        return structure_name in processed

    def _no_cession_result() -> Dict[str, Any]:
        return {
            "applied": False,
            "cession_to_layer_100pct": 0.0,
            "cession_to_reinsurer": 0.0,
        }

    def _process_predecessor_if_needed(structure: Structure) -> None:
        if not structure.has_predecessor():
            return

        predecessor = next(
            (s for s in structures if s.structure_name == structure.predecessor_title),
            None,
        )
        if predecessor:
            process_structure(predecessor)

    def _handle_no_matching_condition(structure: Structure) -> Dict[str, Any]:
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
        structure: Structure, matched_condition: Condition
    ) -> Dict[str, Any]:
        base_input_exposure = _calculate_input_exposure(
            exposure, structure, structure_outputs
        )

        exposure_components = _calculate_exposure_components(
            policy, base_input_exposure, line_of_business
        )

        includes_hull = (
            matched_condition.includes_hull
            if matched_condition.includes_hull is not None
            else True
        )
        includes_liability = (
            matched_condition.includes_liability
            if matched_condition.includes_liability is not None
            else True
        )

        filtered_exposure = exposure_components.apply_filters(
            includes_hull=includes_hull, includes_liability=includes_liability
        )

        condition_to_apply, rescaling_info = _rescale_condition_if_needed(
            matched_condition, structure, structure_outputs
        )

        ceded_result = apply_condition(
            filtered_exposure, condition_to_apply, structure.type_of_participation
        )

        retained = filtered_exposure - ceded_result["cession_to_layer_100pct"]
        current_retention_pct = _calculate_retention_pct(structure, matched_condition)

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
            input_exposure=filtered_exposure,
            ceded_result=ceded_result,
            matched_condition=matched_condition,
            condition_to_apply=condition_to_apply,
            rescaling_info=rescaling_info,
        )

        processed.add(structure.structure_name)

        return {
            "applied": True,
            "cession_to_layer_100pct": ceded_result["cession_to_layer_100pct"],
            "cession_to_reinsurer": ceded_result["cession_to_reinsurer"],
        }

    total_cession_to_layer_100pct = 0.0
    total_cession_to_reinsurer = 0.0

    for structure in structures:
        result = process_structure(structure)
        if result["applied"]:
            total_cession_to_layer_100pct += result["cession_to_layer_100pct"]
            total_cession_to_reinsurer += result["cession_to_reinsurer"]

    return structures_detail, total_cession_to_layer_100pct, total_cession_to_reinsurer


def _calculate_exposure_components(
    policy: Policy,
    total_exposure: float,
    uw: Optional[str],
) -> ExposureComponents:
    comps = policy.exposure_components(uw or (policy.lob or ""))
    tot = comps.total or 0.0
    if tot == 0.0:
        return ExposureComponents(hull=0.0, liability=0.0)
    return ExposureComponents(
        hull=total_exposure * (comps.hull / tot),
        liability=total_exposure * (comps.liability / tot),
    )


def _calculate_input_exposure(
    base_exposure: float,
    structure: Structure,
    structure_outputs: Dict[str, Dict[str, Any]],
) -> float:
    if structure.has_predecessor() and structure.predecessor_title in structure_outputs:
        return structure_outputs[structure.predecessor_title]["retained"]
    return base_exposure


def _rescale_condition_if_needed(
    matched_condition: Condition,
    structure: Structure,
    structure_outputs: Dict[str, Dict[str, Any]],
) -> tuple[Condition, Optional[Dict[str, Any]]]:
    if (
        not structure.has_predecessor()
        or structure.predecessor_title not in structure_outputs
    ):
        return matched_condition.copy(), None

    predecessor_info = structure_outputs[structure.predecessor_title]
    predecessor_type = predecessor_info.get("type_of_participation")

    if predecessor_type == PRODUCT.QUOTA_SHARE and structure.is_excess_of_loss():
        retention_factor = predecessor_info.get("retention_pct", 1.0)
        return matched_condition.rescale_for_predecessor(retention_factor)

    return matched_condition.copy(), None


def _calculate_retention_pct(
    structure: Structure, matched_condition: Condition
) -> float:
    return structure.calculate_retention_pct(matched_condition)


def _add_structure_detail(
    structures_detail: List[Dict[str, Any]],
    structure: Structure,
    applied: bool,
    input_exposure: float = 0.0,
    ceded_result: Optional[Dict[str, float]] = None,
    matched_condition: Optional[Condition] = None,
    condition_to_apply: Optional[Condition] = None,
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
        "predecessor_title": (
            structure.predecessor_title if structure.has_predecessor() else None
        ),
    }

    if applied and ceded_result:
        detail.update(
            {
                "cession_to_layer_100pct": ceded_result["cession_to_layer_100pct"],
                "cession_to_reinsurer": ceded_result["cession_to_reinsurer"],
                "reinsurer_share": ceded_result["reinsurer_share"],
                "condition": matched_condition,
                "condition_rescaled": condition_to_apply,
                "rescaling_info": rescaling_info,
            }
        )
    else:
        detail.update(
            {
                "cession_to_layer_100pct": 0.0,
                "cession_to_reinsurer": 0.0,
                "reinsurer_share": 0.0,
                "condition": None,
            }
        )

    structures_detail.append(detail)
