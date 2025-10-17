from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Set, Dict, Any
from src.domain.condition import Condition


@dataclass(frozen=True)
class RescalingInfo:
    retention_factor: float
    original_attachment: Optional[float] = None
    rescaled_attachment: Optional[float] = None
    original_limit: Optional[float] = None
    rescaled_limit: Optional[float] = None


@dataclass(frozen=True)
class CessionBreakdown:
    to_layer_100pct: float
    to_reinsurer: float
    reinsurer_share: float


@dataclass(frozen=True)
class StructureInput:
    structure_name: str
    predecessor_title: Optional[str]
    type_of_participation: str
    input_exposure: float
    scope_components: Set[str] = field(
        default_factory=set
    )  # {"hull","liability"} ou vide => "total"


@dataclass(frozen=True)
class StructureOutcome:
    applied: bool
    reason: Optional[str]
    matched_condition: Optional[Condition]
    condition_applied: Optional[Condition]
    rescaling: Optional[RescalingInfo]
    cession: CessionBreakdown
    retained_after: float
    matching_details: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class StructureReport:
    input: StructureInput
    outcome: StructureOutcome


@dataclass
class RunTotals:
    cession_to_layer_100pct: float = 0.0
    cession_to_reinsurer: float = 0.0


@dataclass
class ProgramRunResult:
    structures: List[StructureReport] = field(default_factory=list)
    totals: RunTotals = field(default_factory=RunTotals)

    # Métadonnées pour les cas d'exclusion/inactivité
    exclusion_status: str = "included"  # "included", "inactive", "excluded"
    exclusion_reason: Optional[str] = None
    exposure: Optional[float] = None
    effective_exposure: Optional[float] = None
    insured_name: Optional[str] = None
    policy_inception_date: Optional[str] = None
    policy_expiry_date: Optional[str] = None

    def to_flat_dicts(self) -> List[Dict[str, float | str | bool]]:
        """Vue plate et facile à exporter / logger."""
        out = []
        for r in self.structures:
            # Convertir la condition appliquée en dict si elle existe
            condition_dict = None
            if r.outcome.condition_applied:
                condition_dict = r.outcome.condition_applied.to_dict()

            # Convertir les informations de rescaling en dict si elles existent
            rescaling_dict = None
            if r.outcome.rescaling:
                rescaling_dict = {
                    "retention_factor": r.outcome.rescaling.retention_factor,
                    "original_attachment": r.outcome.rescaling.original_attachment,
                    "rescaled_attachment": r.outcome.rescaling.rescaled_attachment,
                    "original_limit": r.outcome.rescaling.original_limit,
                    "rescaled_limit": r.outcome.rescaling.rescaled_limit,
                }

            out.append(
                {
                    "structure_name": r.input.structure_name,
                    "type_of_participation": r.input.type_of_participation,
                    "predecessor_title": r.input.predecessor_title,
                    "input_exposure": r.input.input_exposure,
                    "scope": (
                        ";".join(sorted(r.input.scope_components))
                        if r.input.scope_components
                        else "total"
                    ),
                    "applied": r.outcome.applied,
                    "reason": r.outcome.reason or "",
                    "cession_to_layer_100pct": r.outcome.cession.to_layer_100pct,
                    "cession_to_reinsurer": r.outcome.cession.to_reinsurer,
                    "reinsurer_share": r.outcome.cession.reinsurer_share,
                    "retained_after": r.outcome.retained_after,
                    "condition": condition_dict,
                    "rescaling_info": rescaling_dict,
                    "matching_details": r.outcome.matching_details,
                }
            )
        return out

    def to_dict(self) -> Dict[str, any]:
        """Convertit le résultat en dictionnaire pour compatibilité avec l'API existante."""
        retained_by_cedant = 0.0
        if (
            self.exposure is not None
            and self.totals.cession_to_layer_100pct is not None
        ):
            retained_by_cedant = self.exposure - self.totals.cession_to_layer_100pct

        return {
            "INSURED_NAME": self.insured_name,
            "exposure": self.exposure,
            "effective_exposure": (
                self.effective_exposure
                if self.effective_exposure is not None
                else self.exposure
            ),
            "cession_to_layer_100pct": self.totals.cession_to_layer_100pct,
            "cession_to_reinsurer": self.totals.cession_to_reinsurer,
            "retained_by_cedant": retained_by_cedant,
            "policy_inception_date": self.policy_inception_date,
            "policy_expiry_date": self.policy_expiry_date,
            "structures_detail": self.to_flat_dicts(),
            "exclusion_status": self.exclusion_status,
            "exclusion_reason": self.exclusion_reason,
        }
