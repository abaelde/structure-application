"""
Tests for Program.describe() method
"""

import io
from src.builders.program_builder import build_program
from src.builders.structure_builder import build_quota_share


def test_program_describe_generates_text():
    """Test that program.describe() generates text output"""
    qs_structure = build_quota_share(
        name="QS_1",
        conditions_config=[
            {
                "cession_pct": 0.25,
                "includes_hull": True,
                "includes_liability": True,
            }
        ],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )
    program = build_program(
        name="Test Program",
        structures=[qs_structure],
        dimension_columns=[],
        underwriting_department="test",
    )

    output = io.StringIO()
    program.describe(file=output)
    output_text = output.getvalue()

    assert len(output_text) > 0
    assert "Test Program" in output_text
