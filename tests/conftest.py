import sys
from pathlib import Path
import pytest
import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_program_path():
    return project_root / "examples" / "programs" / "single_quota_share.xlsx"


@pytest.fixture
def sample_bordereau_path():
    return project_root / "examples" / "bordereaux" / "test" / "bordereau_exemple.csv"


@pytest.fixture
def sample_valid_bordereau_data():
    return pd.DataFrame({
        "policy_id": ["POL-001", "POL-002", "POL-003"],
        "INSURED_NAME": ["COMPANY A", "COMPANY B", "COMPANY C"],
        "BUSCL_COUNTRY_CD": ["US", "FR", "UK"],
        "BUSCL_REGION": ["NA", "EU", "EU"],
        "BUSCL_LIMIT_CURRENCY_CD": ["USD", "EUR", "GBP"],
        "line_of_business": ["Aviation", "Property", "Aviation"],
        "exposition": [100.5, 25.5, 30.0],
        "INCEPTION_DT": ["2024-01-01", "2024-02-01", "2024-03-01"],
        "EXPIRE_DT": ["2024-12-31", "2025-01-31", "2025-02-28"],
    })

