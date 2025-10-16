from typing import Dict, Any, Set, Optional
from src.domain import PRODUCT, Structure, Condition, Program
from src.domain.policy import Policy
from .condition_matcher import match_condition
from .cession_calculator import apply_condition
from src.engine.results import (
    ProgramRunResult, RunTotals, StructureReport, StructureInput,
    StructureOutcome, CessionBreakdown, RescalingInfo
)


class StructureProcessor:
    """Traitement des structures avec sorties fortement typées."""

    def __init__(self, policy: Policy, program: Program):
        self.policy = policy
        self.program = program
        self.structures = program.structures
        self.dimension_columns = program.dimension_columns
        
        if not program.underwriting_department:
            raise ValueError("Program must have an underwriting_department")
        self.uw_dept = program.underwriting_department
        self.base_bundle = policy.exposure_bundle(self.uw_dept)

        # Mémorise l'état utile pour le chaînage (retention, type, etc.)
        self._state_by_structure: Dict[str, Dict[str, Any]] = {}
        self._processed: Set[str] = set()

    # ─── API principale ───────────────────────────────────────────────────
    def process_structures(self) -> ProgramRunResult:
        run = ProgramRunResult()

        for structure in self.structures:
            report = self._process_one(structure)
            run.structures.append(report)
            if report.outcome.applied:
                run.totals = RunTotals(
                    cession_to_layer_100pct=run.totals.cession_to_layer_100pct + report.outcome.cession.to_layer_100pct,
                    cession_to_reinsurer=run.totals.cession_to_reinsurer + report.outcome.cession.to_reinsurer,
                )
        return run

    # ─── Détails par structure ────────────────────────────────────────────
    def _process_one(self, structure: Structure) -> StructureReport:
        # 1) Sécurité idempotence
        if structure.structure_name in self._processed:
            return self._report_skipped(structure, reason="already_processed")

        # 2) Garantit le prédécesseur (inuring) si nécessaire
        self._process_predecessor_if_needed(structure)

        # 3) Matching condition le plus spécifique
        matched = match_condition(self.policy, structure.conditions, self.dimension_columns)

        # 4) Calcul de l'exposition d'entrée et du scope (Hull/Liab)
        base_input = self._input_exposure(structure)
        bundle_scaled = self.base_bundle.fraction_to(base_input)
        components = self._components_set(matched)  # vide = "total"
        filtered_exposure = bundle_scaled.select(components if components else None)

        # Si pas de condition → rapport "skipped" mais avec input_exposure explicite
        if matched is None:
            return self._report_skipped(
                structure,
                reason="no_matching_condition",
                input_exposure=filtered_exposure,
                scope_components=components,
            )

        # 5) Rescaling éventuel (XL après QS)
        condition_to_apply, rescaling_info = self._rescale_if_needed(matched, structure)

        # 6) Application du produit
        ceded = apply_condition(filtered_exposure, condition_to_apply, structure.type_of_participation)
        retained = filtered_exposure - ceded["cession_to_layer_100pct"]

        # 7) Mémorise l'état pour les suivants
        self._state_by_structure[structure.structure_name] = {
            "retained": retained,
            "retention_pct": structure.calculate_retention_pct(matched),
            "type_of_participation": structure.type_of_participation,
        }
        self._processed.add(structure.structure_name)

        # 8) Bâtit le rapport typé
        report = StructureReport(
            input=StructureInput(
                structure_name=structure.structure_name,
                predecessor_title=structure.predecessor_title,
                type_of_participation=structure.type_of_participation,
                input_exposure=filtered_exposure,
                scope_components=components,
            ),
            outcome=StructureOutcome(
                applied=True,
                reason=None,
                matched_condition=matched,
                condition_applied=condition_to_apply,
                rescaling=RescalingInfo(**rescaling_info) if rescaling_info else None,
                cession=CessionBreakdown(
                    to_layer_100pct=ceded["cession_to_layer_100pct"],
                    to_reinsurer=ceded["cession_to_reinsurer"],
                    reinsurer_share=ceded["reinsurer_share"],
                ),
                retained_after=retained,
            ),
        )
        return report

    # ─── Sous-étapes explicites ───────────────────────────────────────────
    def _process_predecessor_if_needed(self, structure: Structure) -> None:
        if not structure.has_predecessor():
            return
        pred_name = structure.predecessor_title
        if pred_name in self._processed:
            return
        predecessor = next((s for s in self.structures if s.structure_name == pred_name), None)
        if predecessor:
            self._process_one(predecessor)

    def _input_exposure(self, structure: Structure) -> float:
        """Total d'entrée de la structure (avant filtrage Hull/Liab)."""
        if structure.has_predecessor() and structure.predecessor_title in self._state_by_structure:
            return self._state_by_structure[structure.predecessor_title]["retained"]
        return self.base_bundle.total

    def _components_set(self, matched: Optional[Condition]) -> Set[str]:
        """Scope d'exposition explicite pour Aviation ; vide = 'total'."""
        if self.uw_dept.lower() != "aviation": # AURE : use of enuls ?
            return set()
        inc_h = True if matched is None or matched.includes_hull is None else bool(matched.includes_hull)
        inc_l = True if matched is None or matched.includes_liability is None else bool(matched.includes_liability)
        include: Set[str] = set()
        if inc_h: include.add("hull")
        if inc_l: include.add("liability")
        return include

    def _rescale_if_needed(self, matched: Condition, structure: Structure) -> tuple[Condition, Optional[Dict[str, Any]]]:
        """Rescale XL si prédécesseur QS ; renvoie (condition_à_appliquer, rescaling_info|None)."""
        if not structure.has_predecessor() or structure.predecessor_title not in self._state_by_structure:
            return matched.copy(), None
        pred = self._state_by_structure[structure.predecessor_title]
        if pred.get("type_of_participation") == PRODUCT.QUOTA_SHARE and structure.is_excess_of_loss():
            retention_factor = pred.get("retention_pct", 1.0)
            return matched.rescale_for_predecessor(retention_factor)
        return matched.copy(), None

    # ─── Rapports "skipped" homogènes ─────────────────────────────────────
    def _report_skipped(
        self,
        structure: Structure,
        *,
        reason: str,
        input_exposure: Optional[float] = None,
        scope_components: Optional[Set[str]] = None,
    ) -> StructureReport:
        base_input = self._input_exposure(structure)
        if input_exposure is None:
            # Sans condition, on prend le total (ou la somme des composants en aviation)
            input_exposure = self.base_bundle.fraction_to(base_input).select(None)
        return StructureReport(
            input=StructureInput(
                structure_name=structure.structure_name,
                predecessor_title=structure.predecessor_title,
                type_of_participation=structure.type_of_participation,
                input_exposure=input_exposure,
                scope_components=scope_components or set(),
            ),
            outcome=StructureOutcome(
                applied=False,
                reason=reason,
                matched_condition=None,
                condition_applied=None,
                rescaling=None,
                cession=CessionBreakdown(0.0, 0.0, 0.0),
                retained_after=input_exposure,
            ),
        )


