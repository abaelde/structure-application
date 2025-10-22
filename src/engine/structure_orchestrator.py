from typing import Dict, Any, Set, Optional
from src.domain import PRODUCT, Structure, Condition, Program
from src.domain.policy import Policy
from .condition_matcher import match_condition, match_condition_with_details
from .cession_calculator import apply_condition
from src.engine.results import (
    ProgramRunResult,
    RunTotals,
    StructureRun,
    RescalingInfo,
)
from src.engine.results_terms import create_terms_from_condition, create_empty_terms


class StructureProcessor:
    """Traitement des structures avec sorties fortement typées."""

    def __init__(
        self,
        policy: Policy,
        program: Program,
        *,
        calculation_date: Optional[str] = None,
    ):
        self.policy = policy
        self.program = program
        self.structures = program.structures
        self.dimension_columns = program.dimension_columns
        self.calculation_date = calculation_date

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
            # Filtre multi-année (RA/LO) piloté par calculation_date
            if not structure.is_applicable(
                self.policy,
                evaluation_date=self.calculation_date,
            ):
                run.structures.append(
                    self._report_skipped(
                        structure,
                        reason="out_of_period",
                        input_exposure=self.base_bundle.total,
                        scope_components=set(),
                        matching_details={"claim_basis": structure.claim_basis},
                    )
                )
                continue
            run_obj = self._process_one(structure)
            run.structures.append(run_obj)
            if run_obj.applied:
                run.totals.ceded_to_layer_100pct += run_obj.ceded_to_layer_100pct
                run.totals.ceded_to_reinsurer += run_obj.ceded_to_reinsurer
        return run

    # ─── Détails par structure ────────────────────────────────────────────
    def _process_one(self, structure: Structure) -> StructureRun:
        # 1) Sécurité idempotence
        if structure.structure_name in self._processed:
            return self._report_skipped(structure, reason="already_processed")

        # 1bis) Garde au cas où un prédécesseur serait invoqué directement
        if not structure.is_applicable(
            self.policy,
            evaluation_date=self.calculation_date,
        ):
            return self._report_skipped(
                structure,
                reason="out_of_period",
                input_exposure=self.base_bundle.total,
                scope_components=set(),
                matching_details={"claim_basis": structure.claim_basis},
            )

        # 2) Garantit le prédécesseur (inuring) si nécessaire
        self._process_predecessor_if_needed(structure)

        # 3) Matching condition le plus spécifique avec détails
        matched, matching_details = match_condition_with_details(
            self.policy, structure.conditions, self.dimension_columns
        )

        # 4) Calcul de l'exposition d'entrée et du scope (Hull/Liab)
        base_input = self._input_exposure(structure)
        bundle_scaled = self.base_bundle.fraction_to(base_input)
        components = self._components_set(matched)  # vide = "total"
        filtered_exposure = bundle_scaled.select(components if components else None)

        # Si pas de condition → utiliser les valeurs par défaut de la structure
        if matched is None:
            matched = structure.create_default_condition()
            # Mettre à jour les détails de matching pour indiquer qu'on utilise les valeurs par défaut
            matching_details["matched_condition"] = matched
            matching_details["matching_score"] = 0.0
            matching_details["using_default_values"] = True
        else:
            # Vérifier si la condition matchée est équivalente aux valeurs par défaut
            # (pas de contraintes spécifiques sur les dimensions)
            is_equivalent_to_default = self._is_condition_equivalent_to_default(matched, structure)
            if is_equivalent_to_default:
                matching_details["using_default_values"] = True

        # 5) Rescaling éventuel (XL après QS)
        condition_to_apply, rescaling_info = self._rescale_if_needed(matched, structure)

        # 6) Application du produit
        ceded = apply_condition(
            filtered_exposure, condition_to_apply, structure.type_of_participation
        )
        retained = filtered_exposure - ceded["ceded_to_layer_100pct"]

        # 7) Mémorise l'état pour les suivants
        self._state_by_structure[structure.structure_name] = {
            "retained": retained,
            "retention_pct": structure.calculate_retention_pct(matched),
            "type_of_participation": structure.type_of_participation,
        }
        self._processed.add(structure.structure_name)

        # optionnel: renseigner metrics pour plus de granularité (exposition par composante)
        metrics = {}
        if self.uw_dept.lower() == "aviation":
            # injecter les inputs Hull / Liability si disponible
            bundle_scaled = self.base_bundle.fraction_to(
                self._input_exposure(structure)
            )
            metrics = {
                "hull_input": (
                    bundle_scaled.components.get("hull", 0.0)
                    if bundle_scaled.components
                    else 0.0
                ),
                "liability_input": (
                    bundle_scaled.components.get("liability", 0.0)
                    if bundle_scaled.components
                    else 0.0
                ),
            }

        # 8) Bâtit le StructureRun
        run_obj = StructureRun(
            structure_name=structure.structure_name,
            type_of_participation=structure.type_of_participation,
            predecessor_title=structure.predecessor_title,
            claim_basis=structure.claim_basis,
            period_start=str(structure.inception_date),
            period_end=str(structure.expiry_date),
            applied=True,
            reason=None,
            scope_components=components,
            input_exposure=filtered_exposure,
            matched_condition=matched,
            terms=create_terms_from_condition(matched, structure.type_of_participation),
            rescaling=RescalingInfo(**rescaling_info) if rescaling_info else None,
            ceded_to_layer_100pct=ceded["ceded_to_layer_100pct"],
            ceded_to_reinsurer=ceded["ceded_to_reinsurer"],
            retained_after=retained,
            matching_details=matching_details,
            metrics=metrics,
        )
        return run_obj

    # ─── Sous-étapes explicites ───────────────────────────────────────────
    def _process_predecessor_if_needed(self, structure: Structure) -> None:
        if not structure.has_predecessor():
            return
        pred_name = structure.predecessor_title
        if pred_name in self._processed:
            return
        predecessor = next(
            (s for s in self.structures if s.structure_name == pred_name), None
        )
        if predecessor:
            self._process_one(predecessor)

    def _input_exposure(self, structure: Structure) -> float:
        """Total d'entrée de la structure (avant filtrage Hull/Liab)."""
        if (
            structure.has_predecessor()
            and structure.predecessor_title in self._state_by_structure
        ):
            return self._state_by_structure[structure.predecessor_title]["retained"]
        return self.base_bundle.total

    def _components_set(self, matched: Optional[Condition]) -> Set[str]:
        """Scope d'exposition explicite pour Aviation ; vide = 'total'."""
        # Hors aviation : pas de composants
        if self.uw_dept.lower() != "aviation":
            return set()

        # Si aucune condition ne matche, on applique sur le total (hull+liab)
        if matched is None:
            return {"hull", "liability"}

        # Ici, on exige des bool explicites (serializer les garantit)
        include = set()
        if matched.includes_hull:
            include.add("hull")
        if matched.includes_liability:
            include.add("liability")
        return include

    def _rescale_if_needed(
        self, matched: Condition, structure: Structure
    ) -> tuple[Condition, Optional[Dict[str, Any]]]:
        """Rescale XL si prédécesseur QS ; renvoie (condition_à_appliquer, rescaling_info|None).

        NOTE: Le rescaling est temporairement désactivé. Pour le réactiver, décommenter le code ci-dessous.
        """
        # Rescaling temporairement désactivé
        return matched.copy(), None

        # Code original du rescaling (commenté pour désactivation temporaire):
        # if (
        #     not structure.has_predecessor()
        #     or structure.predecessor_title not in self._state_by_structure
        # ):
        #     return matched.copy(), None
        # pred = self._state_by_structure[structure.predecessor_title]
        # if (
        #     pred.get("type_of_participation") == PRODUCT.QUOTA_SHARE
        #     and structure.is_excess_of_loss()
        # ):
        #     retention_factor = pred.get("retention_pct", 1.0)
        #     return matched.rescale_for_predecessor(retention_factor)
        # return matched.copy(), None

    # ─── Rapports "skipped" homogènes ─────────────────────────────────────
    def _report_skipped(
        self,
        structure: Structure,
        *,
        reason: str,
        input_exposure: Optional[float] = None,
        scope_components: Optional[Set[str]] = None,
        matching_details: Optional[Dict[str, Any]] = None,
    ) -> StructureRun:
        base_input = self._input_exposure(structure)
        if input_exposure is None:
            # Sans condition, on prend le total (ou la somme des composants en aviation)
            input_exposure = self.base_bundle.fraction_to(base_input).select(None)

        return StructureRun(
            structure_name=structure.structure_name,
            type_of_participation=structure.type_of_participation,
            predecessor_title=structure.predecessor_title,
            claim_basis=structure.claim_basis,
            period_start=str(structure.inception_date),
            period_end=str(structure.expiry_date),
            applied=False,
            reason=reason,
            scope_components=scope_components or set(),
            input_exposure=input_exposure,
            matched_condition=None,
            terms=create_empty_terms(structure.type_of_participation),
            rescaling=None,
            ceded_to_layer_100pct=0.0,
            ceded_to_reinsurer=0.0,
            retained_after=input_exposure,
            matching_details=matching_details,
            metrics={},
        )

    def _is_condition_equivalent_to_default(self, condition: Condition, structure: Structure) -> bool:
        """
        Détermine si une condition est équivalente aux valeurs par défaut de la structure.
        Une condition est considérée comme équivalente aux valeurs par défaut si :
        1. Elle n'a aucune contrainte sur les dimensions (toutes les dimensions sont None)
        2. ET elle a les mêmes valeurs que les valeurs par défaut de la structure
        """
        # Vérifier qu'aucune dimension n'est contrainte
        for dimension in self.dimension_columns:
            if condition.has_dimension(dimension):
                return False  # Cette condition a des contraintes spécifiques
        
        # Vérifier que les valeurs correspondent aux valeurs par défaut de la structure
        if structure.type_of_participation == PRODUCT.QUOTA_SHARE:
            # Pour quota share, comparer cession_pct et signed_share
            if condition.cession_pct != structure.cession_pct:
                return False
            if condition.signed_share != structure.signed_share:
                return False
        elif structure.type_of_participation == PRODUCT.EXCESS_OF_LOSS:
            # Pour excess of loss, comparer attachment et limit
            if condition.attachment != structure.attachment:
                return False
            if condition.limit != structure.limit:
                return False
            if condition.signed_share != structure.signed_share:
                return False
        
        return True
