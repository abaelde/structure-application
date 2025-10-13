import pandas as pd
import pytest
from pathlib import Path
from src.loaders import ProgramLoader
from src.engine import apply_program_to_bordereau


def test_double_quota_share_parallel():
    """
    Test avec deux quota shares appliqués en parallèle
    
    STRUCTURE DU PROGRAMME:
    - QS_10% : Quota Share 10% (reinsurer share 100%)
    - QS_15% : Quota Share 15% (reinsurer share 100%)
    
    BORDEREAU:
    - Une seule police avec 1,000,000 d'exposition
    
    CALCUL ATTENDU:
    - Exposition brute: 1,000,000
    - Cession QS_10% (10%): 100,000
    - Cession QS_15% (15%): 150,000
    - Cession totale: 250,000 (10% + 15% = 25%)
    - Retenu (75%): 750,000
    
    PRINCIPE:
    - Les deux quota shares s'appliquent sur la même exposition brute
    - Les cessions s'additionnent
    - Retenu = Exposition brute - Total des cessions
    """
    program_path = Path("tests/integration/fixtures/programs/double_quota_share.xlsx")
    
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
    expected_cession_qs_10 = exposure * 0.10
    expected_cession_qs_15 = exposure * 0.15
    expected_total_cession = expected_cession_qs_10 + expected_cession_qs_15
    expected_retained = exposure - expected_total_cession
    tolerance = 1
    
    assert result["exposure"] == exposure
    assert abs(result["cession_to_layer_100pct"] - expected_total_cession) < tolerance
    assert abs(result["retained_by_cedant"] - expected_retained) < tolerance
    
    total = result["cession_to_layer_100pct"] + result["retained_by_cedant"]
    assert abs(result["exposure"] - total) < tolerance
    
    assert len(structures_detail) >= 2
    applied_structures = [s for s in structures_detail if s["applied"]]
    assert len(applied_structures) == 2
    
    qs_10_detail = next((s for s in applied_structures if "QS_10" in s.get("structure_name", "")), None)
    qs_15_detail = next((s for s in applied_structures if "QS_15" in s.get("structure_name", "")), None)
    
    assert qs_10_detail is not None
    assert qs_15_detail is not None
    
    assert abs(qs_10_detail.get("cession_to_layer_100pct", 0) - expected_cession_qs_10) < tolerance
    assert abs(qs_15_detail.get("cession_to_layer_100pct", 0) - expected_cession_qs_15) < tolerance

