import pandas as pd
import pytest
from pathlib import Path
from src.loaders import ProgramLoader
from src.engine import apply_program_to_bordereau


def test_single_line_quota_share_basic():
    """
    Test simple : Application d'un Quota Share 30% sur une unique ligne de bordereau
    
    STRUCTURE DU PROGRAMME:
    - QS_30% : Quota Share 30% (reinsurer share 100%)
    
    BORDEREAU:
    - Une seule police avec 1,000,000 d'exposition
    
    CALCUL ATTENDU:
    - Exposition brute: 1,000,000
    - Cession (30%): 300,000
    - Retenu (70%): 700,000
    """
    program_path = Path("examples/programs/single_quota_share.xlsx")
    
    if not program_path.exists():
        pytest.skip(f"Programme de test non trouvé: {program_path}")
    
    loader = ProgramLoader(program_path)
    program = loader.get_program()
    
    test_data = {
        "policy_id": ["POL-001"],
        "INSURED_NAME": ["COMPANY TEST"],
        "exposition": [1_000_000],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2025-01-01"],
        "BUSCL_EXCLUDE_CD": [None],
        "BUSCL_ENTITY_NAME_CED": [None],
        "POL_RISK_NAME_CED": [None],
        "BUSCL_COUNTRY_CD": ["US"],
        "BUSCL_REGION": [None],
        "BUSCL_CLASS_OF_BUSINESS_1": [None],
        "BUSCL_CLASS_OF_BUSINESS_2": [None],
        "BUSCL_CLASS_OF_BUSINESS_3": [None],
        "BUSCL_LIMIT_CURRENCY_CD": ["USD"],
    }
    
    bordereau_df = pd.DataFrame(test_data)
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau_df, program, calculation_date=calculation_date
    )
    
    result = results_df.iloc[0]
    structures_detail = result["structures_detail"]
    
    exposure = 1_000_000
    expected_cession_rate = 0.30
    expected_cession = exposure * expected_cession_rate
    expected_retained = exposure * (1 - expected_cession_rate)
    tolerance = 1
    
    assert result["exposure"] == exposure
    assert abs(result["cession_to_layer_100pct"] - expected_cession) < tolerance
    assert abs(result["retained_by_cedant"] - expected_retained) < tolerance
    
    total = result["cession_to_layer_100pct"] + result["retained_by_cedant"]
    assert abs(result["exposure"] - total) < tolerance
    
    assert len(structures_detail) >= 1
    applied_structures = [s for s in structures_detail if s["applied"]]
    assert len(applied_structures) == 1

