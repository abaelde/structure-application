"""
Types typés pour les termes des structures de réassurance.

Ce module définit des dataclasses strictement typées pour les termes
des différentes structures (Quota Share, Excess of Loss), remplaçant
le Dict[str, Any] générique par des types sécurisés.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Union, Dict, Any


@dataclass(frozen=True)
class QSTerms:
    """Termes pour une structure Quota Share."""

    cession_pct: float
    signed_share: float
    limit: Optional[float] = None
    includes_hull: Optional[bool] = None
    includes_liability: Optional[bool] = None


@dataclass(frozen=True)
class XOLTerms:
    """Termes pour une structure Excess of Loss."""

    attachment: float
    limit: float
    signed_share: float
    includes_hull: Optional[bool] = None
    includes_liability: Optional[bool] = None


# Type union pour les termes
StructureTerms = Union[QSTerms, XOLTerms]


def terms_as_dict(terms: StructureTerms) -> Dict[str, Any]:
    """
    Convertit les termes typés en dictionnaire pour l'export.

    Args:
        terms: Termes typés (QSTerms ou XOLTerms)

    Returns:
        Dictionnaire avec les termes aplatissés
    """
    return asdict(terms)


def create_terms_from_condition(condition, structure_type: str) -> StructureTerms:
    """
    Factory method pour créer les termes typés à partir d'une condition.

    Args:
        condition: Condition matched
        structure_type: "quota_share" ou "excess_of_loss"

    Returns:
        Termes typés appropriés
    """
    if structure_type.lower() == "quota_share":
        return QSTerms(
            cession_pct=condition.cession_pct,
            signed_share=condition.signed_share,
            limit=(
                condition.limit
                if hasattr(condition, "limit") and condition.limit is not None
                else None
            ),
            includes_hull=condition.includes_hull,
            includes_liability=condition.includes_liability,
        )
    else:  # excess_of_loss
        return XOLTerms(
            attachment=condition.attachment,
            limit=condition.limit,
            signed_share=condition.signed_share,
            includes_hull=condition.includes_hull,
            includes_liability=condition.includes_liability,
        )


def create_empty_terms(structure_type: str) -> StructureTerms:
    """
    Crée des termes vides pour les structures non appliquées.

    Args:
        structure_type: "quota_share" ou "excess_of_loss"

    Returns:
        Termes typés avec des valeurs par défaut
    """
    if structure_type.lower() == "quota_share":
        return QSTerms(
            cession_pct=0.0,
            signed_share=0.0,
            limit=None,
            includes_hull=None,
            includes_liability=None,
        )
    else:  # excess_of_loss
        return XOLTerms(
            attachment=0.0,
            limit=0.0,
            signed_share=0.0,
            includes_hull=None,
            includes_liability=None,
        )
