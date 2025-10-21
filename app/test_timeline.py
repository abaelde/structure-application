import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.visuals import build_timeline_figure


class DummyStructure:
    def __init__(self, name, claim_basis, inception, expiry):
        self.structure_name = name
        self.claim_basis = claim_basis
        self.inception_date = inception
        self.expiry_date = expiry


class DummyProgram:
    def __init__(self, structures):
        self.structures = structures


def test_build_timeline_figure_basic():
    """
    Vérifie que build_timeline_figure retourne une Figure valide
    et ne lève pas d'exception avec des dates valides et invalides mélangées.
    """
    structures = [
        DummyStructure("QS_A", "RA", "2024-01-01", "2024-12-31"),
        DummyStructure("XOL_B", "LO", "2024-03-01", "2025-03-01"),
        DummyStructure("BROKEN", "LO", None, None),
    ]
    program = DummyProgram(structures)
    fig = build_timeline_figure(program, "2024-06-01")
    assert fig is not None
    # Plotly Figure exposes data/layout attributes
    assert hasattr(fig, "data") and hasattr(fig, "layout")
