"""
Builders for creating Program, Structure, and condition objects directly in memory.

These builders allow creating test programs,
making tests faster and more focused on business logic.
"""

from .condition_builder import build_condition
from .structure_builder import build_quota_share, build_excess_of_loss
from .program_builder import build_program

__all__ = [
    "build_condition",
    "build_quota_share",
    "build_excess_of_loss",
    "build_program",
]
