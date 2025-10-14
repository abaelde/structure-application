"""
Tests for Program.describe() method
"""
import io
from tests.builders.program_builder import build_program
from tests.builders.structure_builder import build_quota_share


def test_program_describe_generates_text():
    """Test that program.describe() generates text output"""
    qs_structure = build_quota_share(
        name="QS_1",
        sections_config=[{
            "cession_pct": 0.25,
            "includes_hull": True,
            "includes_liability": True,
        }]
    )
    program = build_program(
        name="Test Program",
        structures=[qs_structure],
        dimension_columns=[],
        underwriting_department="test"
    )
    
    output = io.StringIO()
    program.describe(file=output)
    output_text = output.getvalue()
    
    assert len(output_text) > 0
    assert "Test Program" in output_text

