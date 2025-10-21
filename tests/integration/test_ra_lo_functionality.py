import pandas as pd
from src.engine import apply_program
from src.domain.policy import Policy
from src.domain.structure import Structure
from src.domain.condition import Condition
from src.domain.constants import CLAIM_BASIS, PRODUCT
from src.domain.program import Program


def test_risk_attaching_based_on_policy_inception():
    """
    Test Risk Attaching : La structure s'applique selon la date d'inception de la police

    SCÉNARIO:
    - Structure RA avec période 2024-01-01 à 2025-01-01
    - Police A : inception 2024-03-01 (dans la période) → structure applicable
    - Police B : inception 2025-03-01 (hors période) → structure non applicable

    CALCULS ATTENDUS:
    - Police A : QS 25% sur 65M = 16.25M cédé
    - Police B : structure non applicable (out_of_period)
    """

    # Créer une condition QS 25%
    condition = Condition.from_dict(
        {
            "CESSION_PCT": 0.25,
            "SIGNED_SHARE_PCT": 1.0,
            "INCLUDES_HULL": True,
            "INCLUDES_LIABILITY": True,
        }
    )

    # Créer structure RA avec période 2024
    structure_ra = Structure(
        structure_name="QS_RA_2024",
        contract_order=1,
        type_of_participation=PRODUCT.QUOTA_SHARE,
        conditions=[condition],
        claim_basis=CLAIM_BASIS.RISK_ATTACHING,
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    # Créer le programme
    program = Program(
        name="Test RA Program",
        underwriting_department="aviation",
        structures=[structure_ra],
        dimension_columns=[],
    )

    # Police A : inception dans la période RA
    policy_a_data = {
        "INSURED_NAME": "Company A",
        "INCEPTION_DT": pd.Timestamp("2024-03-01"),
        "EXPIRE_DT": pd.Timestamp("2025-03-01"),
        "HULL_LIMIT": 100_000_000,
        "LIABILITY_LIMIT": 500_000_000,
        "HULL_SHARE": 0.15,
        "LIABILITY_SHARE": 0.10,
    }
    policy_a = Policy(policy_a_data)

    # Police B : inception hors période RA
    policy_b_data = {
        "INSURED_NAME": "Company B",
        "INCEPTION_DT": pd.Timestamp("2025-03-01"),
        "EXPIRE_DT": pd.Timestamp("2026-03-01"),
        "HULL_LIMIT": 100_000_000,
        "LIABILITY_LIMIT": 500_000_000,
        "HULL_SHARE": 0.15,
        "LIABILITY_SHARE": 0.10,
    }
    policy_b = Policy(policy_b_data)

    # Test avec calculation_date dans la période des structures
    calculation_date = "2024-06-15"

    # Police A : doit s'appliquer (inception dans période RA)
    result_a = apply_program(policy_a, program, calculation_date=calculation_date)
    assert len(result_a.structures) == 1
    structure_result_a = result_a.structures[0]
    assert structure_result_a.structure_name == "QS_RA_2024"
    assert structure_result_a.applied is True
    assert structure_result_a.reason is None
    assert abs(structure_result_a.ceded_to_reinsurer - 16_250_000) < 1

    # Police B : ne doit pas s'appliquer (inception hors période RA)
    result_b = apply_program(policy_b, program, calculation_date=calculation_date)
    assert len(result_b.structures) == 1
    structure_result_b = result_b.structures[0]
    assert structure_result_b.structure_name == "QS_RA_2024"
    assert structure_result_b.applied is False
    assert structure_result_b.reason == "out_of_period"
    assert structure_result_b.matching_details["claim_basis"] == "risk_attaching"


def test_loss_occurring_based_on_calculation_date():
    """
    Test Loss Occurring : La structure s'applique selon la date de calcul

    SCÉNARIO:
    - Structure LO avec période 2024-01-01 à 2025-01-01
    - Même police avec inception 2024-03-01
    - Test avec calculation_date dans la période → structure applicable
    - Test avec calculation_date hors période → structure non applicable

    CALCULS ATTENDUS:
    - calculation_date dans période : QS 30% sur 65M = 19.5M cédé
    - calculation_date hors période : structure non applicable (out_of_period)
    """

    # Créer une condition QS 30%
    condition = Condition.from_dict(
        {
            "CESSION_PCT": 0.30,
            "SIGNED_SHARE_PCT": 1.0,
            "INCLUDES_HULL": True,
            "INCLUDES_LIABILITY": True,
        }
    )

    # Créer structure LO avec période 2024
    structure_lo = Structure(
        structure_name="QS_LO_2024",
        contract_order=1,
        type_of_participation=PRODUCT.QUOTA_SHARE,
        conditions=[condition],
        claim_basis=CLAIM_BASIS.LOSS_OCCURRING,
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    # Créer le programme
    program = Program(
        name="Test LO Program",
        underwriting_department="aviation",
        structures=[structure_lo],
        dimension_columns=[],
    )

    # Police avec inception dans la période
    policy_data = {
        "INSURED_NAME": "Company C",
        "INCEPTION_DT": pd.Timestamp("2024-03-01"),
        "EXPIRE_DT": pd.Timestamp("2025-03-01"),
        "HULL_LIMIT": 100_000_000,
        "LIABILITY_LIMIT": 500_000_000,
        "HULL_SHARE": 0.15,
        "LIABILITY_SHARE": 0.10,
    }
    policy = Policy(policy_data)

    # Test 1 : calculation_date dans la période LO
    calculation_date_in_period = "2024-06-15"
    result_in_period = apply_program(
        policy, program, calculation_date=calculation_date_in_period
    )

    assert len(result_in_period.structures) == 1
    structure_result_in = result_in_period.structures[0]
    assert structure_result_in.structure_name == "QS_LO_2024"
    assert structure_result_in.applied is True
    assert structure_result_in.reason is None
    assert abs(structure_result_in.ceded_to_reinsurer - 19_500_000) < 1

    # Test 2 : calculation_date hors période LO
    calculation_date_out_period = "2023-06-15"
    result_out_period = apply_program(
        policy, program, calculation_date=calculation_date_out_period
    )

    assert len(result_out_period.structures) == 1
    structure_result_out = result_out_period.structures[0]
    assert structure_result_out.structure_name == "QS_LO_2024"
    assert structure_result_out.applied is False
    assert structure_result_out.reason == "out_of_period"
    assert structure_result_out.matching_details["claim_basis"] == "loss_occurring"
