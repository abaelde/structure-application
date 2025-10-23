import pandas as pd
from src.engine import apply_program_to_bordereau
from src.domain.bordereau import Bordereau
from src.builders import build_quota_share, build_excess_of_loss, build_program


def test_quota_share_then_excess_of_loss_without_rescaling():
    """
    Test complet grandeur réelle : QS → XL SANS rescaling

    STRUCTURE DU PROGRAMME:
    1. QS_30% : Quota Share 30% (reinsurer share 100%)
    2. XOL_50xs20 : Excess of Loss 50M xs 20M (reinsurer share 100%) - inuring sur QS_30%

    POLICES DE TEST:
    - Policy A: 50M  → En dessous de l'attachment XL après QS
    - Policy B: 100M → Partiellement dans la layer XL après QS
    - Policy C: 150M → Complètement dans et au-dessus de la layer XL après QS

    CALCULS ATTENDUS (SANS RESCALING):

    Policy A (50M):
    ---------------
    QS_30%: 50M * 30% = 15M cédé, 35M retenu
    XOL_50xs20 sur 35M: attachment=20M (NON rescalé), limit=50M (NON rescalé)
        → 35M < 20M? Non, 35M > 20M, donc cession = min(35M - 20M, 50M) = 15M
    Total cession: 15M (QS) + 15M (XL) = 30M
    Retained: 50M - 30M = 20M

    Policy B (100M):
    ----------------
    QS_30%: 100M * 30% = 30M cédé, 70M retenu
    XOL_50xs20 sur 70M: attachment=20M (NON rescalé), limit=50M (NON rescalé)
        → 70M > 20M, cession = min(70M - 20M, 50M) = min(50M, 50M) = 50M
    Total cession: 30M (QS) + 50M (XL) = 80M
    Retained: 100M - 80M = 20M

    Policy C (150M):
    ----------------
    QS_30%: 150M * 30% = 45M cédé, 105M retenu
    XOL_50xs20 sur 105M: attachment=20M (NON rescalé), limit=50M (NON rescalé)
        → 105M > 20M, cession = min(105M - 20M, 50M) = min(85M, 50M) = 50M
    Total cession: 45M (QS) + 50M (XL) = 95M
    Retained: 150M - 95M = 55M
    """

    qs = build_quota_share(
        name="QS_30%",
        cession_pct=0.30,
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )
    xl = build_excess_of_loss(
        name="XOL_50xs20",
        attachment=20_000_000,
        limit=50_000_000,
        predecessor_title="QS_30%",
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    program = build_program(
        name="TEST_QS_XL", structures=[qs, xl], main_currency="EUR", underwriting_department="test"
    )

    # 2. Créer le bordereau de test

    test_data = {
        "INSURED_NAME": ["Company A", "Company B", "Company C"],
        "exposure": [50_000_000, 100_000_000, 150_000_000],
        "INCEPTION_DT": ["2024-01-01", "2024-01-01", "2024-01-01"],
        "EXPIRE_DT": ["2025-01-01", "2025-01-01", "2025-01-01"],
    }

    bordereau_df = pd.DataFrame(test_data)

    # 3. Application du programme
    bordereau = Bordereau(bordereau_df, uw_dept="test")
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date=calculation_date
    )

    # Policy A (50M)
    result_a = results_df.iloc[0]

    # QS: 50M * 30% = 15M, retenu = 35M
    # XL sur 35M: attachment NON rescalé = 20M, limit NON rescalé = 50M
    # Cession XL = min(35M - 20M, 50M) = 15M
    # Total cession = 15M + 15M = 30M

    expected_cession_a = 30_000_000
    tolerance = 100

    assert abs(result_a["cession_to_layer_100pct"] - expected_cession_a) < tolerance

    # Policy B (100M)
    result_b = results_df.iloc[1]

    # QS: 100M * 30% = 30M, retenu = 70M
    # XL sur 70M: attachment NON rescalé = 20M, limit NON rescalé = 50M
    # Cession XL = min(70M - 20M, 50M) = 50M
    # Total cession = 30M + 50M = 80M

    expected_cession_b = 80_000_000

    assert abs(result_b["cession_to_layer_100pct"] - expected_cession_b) < tolerance

    # Policy C (150M)
    result_c = results_df.iloc[2]

    # QS: 150M * 30% = 45M, retenu = 105M
    # XL sur 105M: attachment NON rescalé = 20M, limit NON rescalé = 50M
    # Cession XL = min(105M - 20M, 50M) = 50M
    # Total cession = 45M + 50M = 95M

    expected_cession_c = 95_000_000

    assert abs(result_c["cession_to_layer_100pct"] - expected_cession_c) < tolerance

    # Vérification du total
    total_cession_layer = results_df["cession_to_layer_100pct"].sum()
    expected_total = expected_cession_a + expected_cession_b + expected_cession_c
    assert abs(total_cession_layer - expected_total) < tolerance * 3

    # Vérification de la conservation de l'exposure
    for idx in range(len(results_df)):
        result = results_df.iloc[idx]
        exposure = result["exposure"]
        cession = result["cession_to_layer_100pct"]
        retained = result["retained_by_cedant"]

        assert abs(exposure - (cession + retained)) < tolerance


if __name__ == "__main__":
    test_quota_share_then_excess_of_loss_without_rescaling()
