from abc import ABC, abstractmethod
from src.domain.models import condition


class Product(ABC):
    @abstractmethod
    def apply(self, exposure: float, condition: condition) -> float:
        pass

