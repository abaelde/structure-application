import pandas as pd
from src.engine import apply_program_to_bordereau
from src.domain.bordereau import Bordereau
from src.builders import build_quota_share, build_program


def test_policy_expiry_mechanism():
    """
    Test du mécanisme d'expiration des polices

    STRUCTURE DU PROGRAMME:
    - QS_30% : Quota Share 30%

    BORDEREAU:
    - 4 polices avec différentes dates d'expiration

    CALCULS ATTENDUS:
    - Les polices expirées sont marquées "inactive"
    - Les polices actives sont marquées "included"
    - Cession = 0 pour les polices expirées
    """
    qs = build_quota_share(
        name="QS_30",
        cession_pct=0.30,
        claim_basis="risk_attaching",
        inception_date="2023-01-01",
        expiry_date="2027-01-01",
    )
    program = build_program(
        name="TEST_LIFECYCLE", structures=[qs], main_currency="EUR", underwriting_department="test"
    )

    test_data = {
        "INSURED_NAME": ["COMPANY A", "COMPANY B", "COMPANY C", "COMPANY D"],
        "exposure": [1000000, 2000000, 500000, 750000],
        "INCEPTION_DT": ["2024-01-01", "2024-06-01", "2023-01-01", "2025-01-01"],
        "EXPIRE_DT": ["2025-01-01", "2025-06-01", "2024-01-01", "2026-01-01"],
    }

    bordereau_df = pd.DataFrame(test_data)
    bordereau = Bordereau(bordereau_df, uw_dept="test")

    _, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date="2024-06-01"
    )
    assert results_df.loc[0, "exclusion_status"] == "included"
    assert results_df.loc[1, "exclusion_status"] == "included"
    assert results_df.loc[2, "exclusion_status"] == "inactive"
    assert results_df.loc[3, "exclusion_status"] == "included"
    assert (results_df["exclusion_status"] == "included").sum() == 3
    assert (results_df["exclusion_status"] == "inactive").sum() == 1
    assert results_df.loc[2, "cession_to_reinsurer"] == 0

    _, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date="2024-12-31"
    )
    assert results_df.loc[0, "exclusion_status"] == "included"
    assert results_df.loc[1, "exclusion_status"] == "included"
    assert results_df.loc[2, "exclusion_status"] == "inactive"
    assert results_df.loc[3, "exclusion_status"] == "included"
    assert (results_df["exclusion_status"] == "included").sum() == 3
    assert (results_df["exclusion_status"] == "inactive").sum() == 1

    _, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date="2025-01-01"
    )
    assert results_df.loc[0, "exclusion_status"] == "inactive"
    assert results_df.loc[1, "exclusion_status"] == "included"
    assert results_df.loc[2, "exclusion_status"] == "inactive"
    assert results_df.loc[3, "exclusion_status"] == "included"
    assert (results_df["exclusion_status"] == "included").sum() == 2
    assert (results_df["exclusion_status"] == "inactive").sum() == 2
    assert results_df.loc[0, "cession_to_reinsurer"] == 0
    assert results_df.loc[2, "cession_to_reinsurer"] == 0

    _, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date="2025-07-01"
    )
    assert results_df.loc[0, "exclusion_status"] == "inactive"
    assert results_df.loc[1, "exclusion_status"] == "inactive"
    assert results_df.loc[2, "exclusion_status"] == "inactive"
    assert results_df.loc[3, "exclusion_status"] == "included"
    assert (results_df["exclusion_status"] == "included").sum() == 1
    assert (results_df["exclusion_status"] == "inactive").sum() == 3
    assert results_df.loc[0, "cession_to_reinsurer"] == 0
    assert results_df.loc[1, "cession_to_reinsurer"] == 0
    assert results_df.loc[2, "cession_to_reinsurer"] == 0
    assert results_df.loc[3, "cession_to_reinsurer"] > 0


if __name__ == "__main__":
    test_policy_expiry_mechanism()
