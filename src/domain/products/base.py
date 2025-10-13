from abc import ABC, abstractmethod
from src.domain.models import Section


class Product(ABC):
    @abstractmethod
    def apply(self, exposure: float, section: Section) -> float:
        pass

