from typing import Dict, Any
import pandas as pd
import sys

from src.domain import PRODUCT, SECTION_COLS as SC, Program


def write_program_config(program: Program, file=None) -> None:
    """Write program configuration to file. Delegates to Program.describe()"""
    program.describe(file=file)


def display_program(program: Program) -> None:
    """Display program configuration to stdout. Delegates to Program.describe()"""
    program.describe(file=sys.stdout)
