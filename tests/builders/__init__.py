"""
Builders for creating Program, Structure, and Section objects directly in memory.

These builders allow creating test programs without the overhead of Excel I/O,
making tests faster and more focused on business logic.
"""

from .section_builder import build_section, build_exclusion_section
from .structure_builder import build_quota_share, build_excess_of_loss
from .program_builder import build_program

__all__ = [
    "build_section",
    "build_exclusion_section",
    "build_quota_share",
    "build_excess_of_loss",
    "build_program",
]

