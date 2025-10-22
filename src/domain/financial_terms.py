from dataclasses import dataclass, replace
from typing import Optional, Dict, Any

# Mapping des champs de condition vers les attributs du Value Object FinancialTerms
FIELD_TO_TERMS_KEY = {
    "CESSION_PCT": "cession_pct",
    "ATTACHMENT_POINT_100": "attachment",
    "LIMIT_100": "limit",
    "SIGNED_SHARE_PCT": "signed_share",
}


@dataclass(frozen=True)
class FinancialTerms:
    """
    Value Object représentant les termes financiers d'une structure de réassurance.
    
    Centralise la sémantique des termes financiers et fournit des méthodes
    pour la fusion avec des overrides et la conversion vers les formats
    utilisés par le système.
    """
    cession_pct: Optional[float] = None
    attachment: Optional[float] = None
    limit: Optional[float] = None
    signed_share: float = 1.0

    def merge(self, **overrides) -> "FinancialTerms":
        """
        Fusionne les termes actuels avec des overrides.
        
        Args:
            **overrides: Dictionnaire des valeurs à surcharger
            
        Returns:
            Nouvelle instance FinancialTerms avec les overrides appliqués
        """
        clean = {k: v for k, v in overrides.items() if v is not None}
        return replace(self, **clean)

    def to_condition_dict(self) -> Dict[str, Any]:
        """
        Convertit les termes financiers vers le format utilisé dans les conditions.
        
        Returns:
            Dictionnaire avec les clés utilisées par le système de conditions
        """
        return {
            "CESSION_PCT": self.cession_pct,
            "ATTACHMENT_POINT_100": self.attachment,
            "LIMIT_100": self.limit,
            "SIGNED_SHARE_PCT": self.signed_share,
        }

    def diff(self, other: "FinancialTerms") -> Dict[str, Any]:
        """
        Calcule la différence entre deux instances de FinancialTerms.
        
        Args:
            other: Autre instance FinancialTerms à comparer
            
        Returns:
            Dictionnaire contenant uniquement les valeurs qui diffèrent
        """
        a = self.to_condition_dict()
        b = other.to_condition_dict()
        return {k: b[k] for k in a if b[k] is not None and b[k] != a[k]}

    def __str__(self) -> str:
        """Représentation string des termes financiers."""
        parts = []
        if self.cession_pct is not None:
            parts.append(f"cession={self.cession_pct}%")
        if self.attachment is not None:
            parts.append(f"attachment={self.attachment}")
        if self.limit is not None:
            parts.append(f"limit={self.limit}")
        if self.signed_share is not None and self.signed_share != 1.0:
            parts.append(f"share={self.signed_share}")
        return f"FinancialTerms({', '.join(parts)})"
