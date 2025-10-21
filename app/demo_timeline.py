import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from types import SimpleNamespace
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


def main():
    # Jeu de données synthétique couvrant plusieurs cas (dates valides, NaT, etc.)
    structures = [
        DummyStructure("QS_2024", "RA", "2024-01-01", "2024-12-31"),
        DummyStructure("XOL_2024", "LO", "2024-03-01", "2025-03-01"),
        DummyStructure("QS_2025", "RA", "2025-01-01", "2025-12-31"),
        DummyStructure("BROKEN", "LO", None, None),  # Doit être filtré
    ]
    program = DummyProgram(structures)
    calculation_date = "2024-06-01"

    fig = build_timeline_figure(program, calculation_date)
    out_path = PROJECT_ROOT / "output" / "demo_timeline.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path))
    print(f"Timeline figure written to {out_path}")


if __name__ == "__main__":
    main()
