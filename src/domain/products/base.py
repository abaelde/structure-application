from abc import ABC, abstractmethod
from typing import Dict, Any


class Product(ABC):
    @abstractmethod
    def apply(self, exposure: float, section: Dict[str, Any]) -> float:
        pass

