from dataclasses import dataclass


@dataclass
class ExposureComponents:
    hull: float = 0.0
    liability: float = 0.0

    @property
    def total(self) -> float:
        return self.hull + self.liability

    def apply_filters(self, includes_hull: bool, includes_liability: bool) -> float:
        result = 0.0
        if includes_hull:
            result += self.hull
        if includes_liability:
            result += self.liability
        return result
