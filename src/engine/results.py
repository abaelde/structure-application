from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Set, Dict
from src.domain.models import Condition


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
    scope_components: Set[str] = field(default_factory=set)  # {"hull","liability"} ou vide => "total"


@dataclass(frozen=True)
class StructureOutcome:
    applied: bool
    reason: Optional[str]
    matched_condition: Optional[Condition]
    condition_applied: Optional[Condition]
    rescaling: Optional[RescalingInfo]
    cession: CessionBreakdown
    retained_after: float


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

    def to_flat_dicts(self) -> List[Dict[str, float | str | bool]]:
        """Vue plate et facile à exporter / logger."""
        out = []
        for r in self.structures:
            out.append({
                "structure_name": r.input.structure_name,
                "type_of_participation": r.input.type_of_participation,
                "predecessor_title": r.input.predecessor_title,
                "input_exposure": r.input.input_exposure,
                "scope": ";".join(sorted(r.input.scope_components)) if r.input.scope_components else "total",
                "applied": r.outcome.applied,
                "reason": r.outcome.reason or "",
                "cession_to_layer_100pct": r.outcome.cession.to_layer_100pct,
                "cession_to_reinsurer": r.outcome.cession.to_reinsurer,
                "reinsurer_share": r.outcome.cession.reinsurer_share,
                "retained_after": r.outcome.retained_after,
            })
        return out
