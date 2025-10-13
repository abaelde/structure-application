import pandas as pd
from src.engine import apply_program_to_bordereau
from tests.builders import build_quota_share, build_excess_of_loss, build_program


def test_quota_share_then_excess_of_loss_with_rescaling():
    """
    Test complet grandeur réelle : QS → XL avec rescaling
    
    STRUCTURE DU PROGRAMME:
    1. QS_30% : Quota Share 30% (reinsurer share 100%)
    2. XOL_50xs20 : Excess of Loss 50M xs 20M (reinsurer share 100%) - inuring sur QS_30%
    
    POLICES DE TEST:
    - Policy A: 50M  → En dessous de l'attachment XL après QS
    - Policy B: 100M → Partiellement dans la layer XL après QS
    - Policy C: 150M → Complètement dans et au-dessus de la layer XL après QS
    
    CALCULS ATTENDUS:
    
    Policy A (50M):
    ---------------
    QS_30%: 50M * 30% = 15M cédé, 35M retenu
    XOL_50xs20 sur 35M: attachment=20M*(1-30%)=14M, limit=50M*(1-30%)=35M
        → 35M < 14M? Non, 35M > 14M, donc cession = min(35M - 14M, 35M) = 21M
    Total cession: 15M (QS) + 21M (XL) = 36M
    Retained: 50M - 36M = 14M
    
    Policy B (100M):
    ----------------
    QS_30%: 100M * 30% = 30M cédé, 70M retenu
    XOL_50xs20 sur 70M: attachment=14M, limit=35M
        → 70M > 14M, cession = min(70M - 14M, 35M) = min(56M, 35M) = 35M
    Total cession: 30M (QS) + 35M (XL) = 65M
    Retained: 100M - 65M = 35M
    
    Policy C (150M):
    ----------------
    QS_30%: 150M * 30% = 45M cédé, 105M retenu
    XOL_50xs20 sur 105M: attachment=14M, limit=35M
        → 105M > 14M, cession = min(105M - 14M, 35M) = 35M
    Total cession: 45M (QS) + 35M (XL) = 80M
    Retained: 150M - 80M = 70M
    """
    
    qs = build_quota_share(name="QS_30%", cession_pct=0.30)
    xl = build_excess_of_loss(
        name="XOL_50xs20",
        attachment=20_000_000,
        limit=50_000_000,
        predecessor_title="QS_30%"
    )
    
    program = build_program(
        name="TEST_QS_XL",
        structures=[qs, xl]
    )
    
    # 2. Créer le bordereau de test
    
    test_data = {
        "policy_id": ["POL-A", "POL-B", "POL-C"],
        "INSURED_NAME": ["Company A", "Company B", "Company C"],
        "exposition": [50_000_000, 100_000_000, 150_000_000],
        "INCEPTION_DT": ["2024-01-01", "2024-01-01", "2024-01-01"],
        "EXPIRE_DT": ["2025-01-01", "2025-01-01", "2025-01-01"],
        # Toutes les colonnes dimensionnelles requises
        "BUSCL_EXCLUDE_CD": [None, None, None],
        "BUSCL_ENTITY_NAME_CED": [None, None, None],
        "POL_RISK_NAME_CED": [None, None, None],
        "BUSCL_COUNTRY_CD": ["US", "US", "US"],
        "BUSCL_REGION": [None, None, None],
        "BUSCL_CLASS_OF_BUSINESS_1": [None, None, None],
        "BUSCL_CLASS_OF_BUSINESS_2": [None, None, None],
        "BUSCL_CLASS_OF_BUSINESS_3": [None, None, None],
        "BUSCL_LIMIT_CURRENCY_CD": ["USD", "USD", "USD"],
    }
    
    bordereau_df = pd.DataFrame(test_data)
    
    # 3. Application du programme
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau_df, program, calculation_date=calculation_date
    )
    
    # Policy A (50M)
    result_a = results_df.iloc[0]
    
    # QS: 50M * 30% = 15M, retenu = 35M
    # XL sur 35M: attachment rescalé = 20M * 70% = 14M, limit = 35M
    # Cession XL = min(35M - 14M, 35M) = 21M
    # Total cession = 15M + 21M = 36M
    
    expected_cession_a = 36_000_000
    tolerance = 100
    
    assert abs(result_a["cession_to_layer_100pct"] - expected_cession_a) < tolerance
    
    # Policy B (100M)
    result_b = results_df.iloc[1]
    
    # QS: 100M * 30% = 30M, retenu = 70M
    # XL sur 70M: cession = min(70M - 14M, 35M) = 35M
    # Total cession = 30M + 35M = 65M
    
    expected_cession_b = 65_000_000
    
    assert abs(result_b["cession_to_layer_100pct"] - expected_cession_b) < tolerance
    
    # Policy C (150M)
    result_c = results_df.iloc[2]
    
    # QS: 150M * 30% = 45M, retenu = 105M
    # XL sur 105M: cession = min(105M - 14M, 35M) = 35M
    # Total cession = 45M + 35M = 80M
    
    expected_cession_c = 80_000_000
    
    assert abs(result_c["cession_to_layer_100pct"] - expected_cession_c) < tolerance
    
    # Vérification du total
    total_cession_layer = results_df["cession_to_layer_100pct"].sum()
    expected_total = expected_cession_a + expected_cession_b + expected_cession_c
    assert abs(total_cession_layer - expected_total) < tolerance * 3
    
    # Vérification de la conservation de l'exposition
    for idx in range(len(results_df)):
        result = results_df.iloc[idx]
        exposure = result["exposure"]
        cession = result["cession_to_layer_100pct"]
        retained = result["retained_by_cedant"]
        
        assert abs(exposure - (cession + retained)) < tolerance


if __name__ == "__main__":
    test_quota_share_then_excess_of_loss_with_rescaling()

