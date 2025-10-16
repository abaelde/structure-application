from abc import ABC, abstractmethod
from src.domain.models import Condition


class Product(ABC):
    @abstractmethod
    def apply(self, exposure: float, condition: Condition) -> float:
        pass

