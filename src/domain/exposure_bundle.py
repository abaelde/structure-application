from dataclasses import dataclass, field
from typing import Dict, Optional, Set


@dataclass
class ExposureBundle:
    """Conteneur générique d'exposition.
    - total : exposition scalaire
    - components : sous-composantes nommées (ex. {"hull": 15e6, "liability": 50e6})
      Vide pour les LOB qui n'en ont pas besoin (Casualty/Test).
    """

    total: float = 0.0
    components: Dict[str, float] = field(default_factory=dict)

    def fraction_to(self, new_total: float) -> "ExposureBundle":
        """Retourne un bundle dont le total vaut new_total, en conservant les proportions."""
        if self.total <= 0.0 or not self.components:
            return ExposureBundle(total=new_total, components={})
        scale = new_total / self.total
        return ExposureBundle(
            total=new_total,
            components={k: v * scale for k, v in self.components.items()},
        )

    def select(self, include: Optional[Set[str]] = None) -> float:
        """Exposition sur un sous-ensemble de composantes. Sans composantes ou include=None → total."""
        if not self.components or include is None:
            return self.total
        return sum(self.components.get(k, 0.0) for k in include)
