from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Set, Dict, Any, Union
from src.domain.condition import Condition
from .results_terms import StructureTerms, terms_as_dict


@dataclass(frozen=True)
class RescalingInfo:
    retention_factor: float
    original_attachment: Optional[float] = None
    rescaled_attachment: Optional[float] = None
    original_limit: Optional[float] = None
    rescaled_limit: Optional[float] = None


@dataclass(frozen=True)
class StructureRun:
    # --- identité / contexte ---
    structure_name: str
    type_of_participation: str  # "quota_share" | "excess_of_loss"
    predecessor_title: Optional[str]
    claim_basis: str  # "risk_attaching" | "loss_occurring"
    period_start: str  # inception de la structure
    period_end: str  # expiry (exclusive)

    # --- applicabilité ---
    applied: bool
    reason: Optional[
        str
    ]  # "out_of_period" | "no_matching_condition" | "already_processed" | None
    scope_components: Set[str]  # {"hull","liability"} ou vide => "total"

    # --- entrée & termes appliqués ---
    input_exposure: float  # après éventuel filtrage Hull/Liab
    matched_condition: Optional[Condition]  # raw (debug/audit)
    terms: StructureTerms  # Termes typés (QSTerms ou XOLTerms)
    rescaling: Optional[RescalingInfo]  # si activé

    # --- résultat chiffré ---
    ceded_to_layer_100pct: float
    ceded_to_reinsurer: float
    retained_after: float

    # --- espace d'extension libre ---
    matching_details: Optional[Dict[str, Any]] = None
    metrics: Dict[str, float] = field(
        default_factory=dict
    )  # ex: {"hull_input": 11.25e6, "liab_input": 37.5e6}


@dataclass
class RunTotals:
    ceded_to_layer_100pct: float = 0.0
    ceded_to_reinsurer: float = 0.0


@dataclass
class ProgramRunResult:
    structures: List[StructureRun] = field(default_factory=list)
    totals: RunTotals = field(default_factory=RunTotals)

    # Métadonnées pour les cas d'exclusion/inactivité
    exclusion_status: str = "included"  # "included", "inactive", "excluded"
    exclusion_reason: Optional[str] = None
    exposure: Optional[float] = None
    effective_exposure: Optional[float] = None
    insured_name: Optional[str] = None
    policy_inception_date: Optional[str] = None
    policy_expiry_date: Optional[str] = None

    # Vue plate pour export CSV/DF
    def to_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for r in self.structures:
            rows.append(
                {
                    "structure_name": r.structure_name,
                    "type_of_participation": r.type_of_participation,
                    "predecessor_title": r.predecessor_title or "",
                    "claim_basis": r.claim_basis,
                    "period_start": r.period_start,
                    "period_end": r.period_end,
                    "applied": r.applied,
                    "reason": r.reason or "",
                    "scope": (
                        ";".join(sorted(r.scope_components))
                        if r.scope_components
                        else "total"
                    ),
                    "input_exposure": r.input_exposure,
                    "ceded_to_layer_100pct": r.ceded_to_layer_100pct,
                    "ceded_to_reinsurer": r.ceded_to_reinsurer,
                    "retained_after": r.retained_after,
                    # Aplatissement des termes typés
                    **{k: v for k, v in terms_as_dict(r.terms).items()},
                    # compat: exposer la part signée via les termes (entrée), pas comme résultat
                    "reinsurer_signed_share": terms_as_dict(r.terms).get(
                        "signed_share"
                    ),
                    # Metrics libres (si tu veux les garder à plat, tu peux aussi les préfixer)
                    "metrics": r.metrics,
                    "matching_details": r.matching_details,  # utile côté debug/UX
                }
            )
        return rows

    # Vue simplifiée pour export CSV/DF - juste l'exposition par police
    def to_simple_rows(self) -> List[Dict[str, Any]]:
        """
        Retourne une vue simplifiée avec juste l'exposition par police.
        Une ligne par police avec les totaux de cession.
        """
        return [
            {
                "insured_name": self.insured_name,
                "exposure": self.exposure,
                "effective_exposure": (
                    self.effective_exposure
                    if self.effective_exposure is not None
                    else self.exposure
                ),
                "ceded_to_layer_100pct": self.totals.ceded_to_layer_100pct,
                "ceded_to_reinsurer": self.totals.ceded_to_reinsurer,
                "retained_by_cedant": (
                    self.exposure - self.totals.ceded_to_layer_100pct
                    if self.exposure is not None
                    and self.totals.ceded_to_layer_100pct is not None
                    else None
                ),
                "policy_inception_date": self.policy_inception_date,
                "policy_expiry_date": self.policy_expiry_date,
                "exclusion_status": self.exclusion_status,
                "exclusion_reason": self.exclusion_reason,
            }
        ]

    # Vue "legacy" compatible (optionnel)
    def to_dict(self) -> Dict[str, Any]:
        retained_by_cedant = 0.0
        if self.exposure is not None and self.totals.ceded_to_layer_100pct is not None:
            retained_by_cedant = self.exposure - self.totals.ceded_to_layer_100pct

        return {
            "INSURED_NAME": self.insured_name,
            "exposure": self.exposure,
            "effective_exposure": (
                self.effective_exposure
                if self.effective_exposure is not None
                else self.exposure
            ),
            "cession_to_layer_100pct": self.totals.ceded_to_layer_100pct,  # alias legacy
            "cession_to_reinsurer": self.totals.ceded_to_reinsurer,  # alias legacy
            "retained_by_cedant": retained_by_cedant,
            "policy_inception_date": self.policy_inception_date,
            "policy_expiry_date": self.policy_expiry_date,
            "structures_detail": self.to_rows(),  # lisible et plat
            "exclusion_status": self.exclusion_status,
            "exclusion_reason": self.exclusion_reason,
        }
