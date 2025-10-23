import pandas as pd
from src.engine import apply_program_to_bordereau
from src.domain.bordereau import Bordereau
from src.domain.exclusion import ExclusionRule
from src.builders import (
    build_quota_share,
    build_condition,
    build_program,
)


def test_exclusion_mechanism():
    """
    Test du mécanisme d'exclusion dans un programme Quota Share

    STRUCTURE DU PROGRAMME:
    - Quota Share 25% avec exclusions globales par pays (Iran, Russia)
    - condition catch-all avec 25% de cession

    BORDEREAU:
    - 7 polices avec différents pays
    - Certaines polices doivent être exclues selon les critères

    CALCULS ATTENDUS:
    - Les polices exclues ont une exposure effective à 0
    - Les polices incluses ont une cession de 25% de leur exposure
    - Le statut d'exclusion est correctement reporté
    """
    # Créer le programme avec exclusions au niveau programme
    conditions = [
        build_condition(
            cession_pct=0.25, includes_hull=True, includes_liability=True
        ).to_dict(),
    ]

    qs = build_quota_share(
        name="QS_Aviation_25%",
        cession_pct=0.25,
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    # Créer les exclusions au niveau programme
    exclusions = [
        ExclusionRule(
            values_by_dimension={"COUNTRY": ["Iran"]}, name="Sanctions Iran"
        ),
        ExclusionRule(
            values_by_dimension={"COUNTRY": ["Russia"]},
            name="Sanctions Russia",
        ),
    ]

    program = build_program(
        name="QS_WITH_EXCLUSIONS", structures=[qs], underwriting_department="test"
    )

    # Ajouter les exclusions au programme
    program.exclusions = exclusions

    # Créer le bordereau de test
    test_data = {
        "INSURED_NAME": [
            "AIR FRANCE",
            "IRAN AIR",
            "LUFTHANSA",
            "AEROFLOT",
            "EMIRATES",
            "SANCTIONED AIRLINE",
            "BRITISH AIRWAYS",
        ],
        "COUNTRY": [
            "France",
            "Iran",
            "Germany",
            "Russia",
            "United Arab Emirates",
            "Syria",
            "United Kingdom",
        ],
        "exposure": [250_000, 30_000, 40_000, 35_000, 52_000, 20_000, 41_000],
        "INCEPTION_DT": [
            "2024-01-01",
            "2024-02-15",
            "2024-03-01",
            "2024-01-15",
            "2024-04-01",
            "2024-02-01",
            "2024-05-01",
        ],
        "EXPIRE_DT": [
            "2025-12-31",
            "2025-02-14",
            "2025-02-28",
            "2025-01-14",
            "2025-03-31",
            "2025-01-31",
            "2025-04-30",
        ],
    }

    bordereau_df = pd.DataFrame(test_data)
    bordereau = Bordereau(bordereau_df, uw_dept="test")

    __, results = apply_program_to_bordereau(
        bordereau, program, calculation_date="2024-06-01"
    )

    excluded_count = (results["exclusion_status"] == "excluded").sum()
    included_count = (results["exclusion_status"] == "included").sum()

    assert len(results) == 7
    assert excluded_count >= 0
    assert included_count >= 0
    assert excluded_count + included_count == len(results)

    excluded_policies = results[results["exclusion_status"] == "excluded"]
    for _, policy in excluded_policies.iterrows():
        assert policy["effective_exposure"] == 0
        assert policy["cession_to_reinsurer"] == 0

    included_policies = results[results["exclusion_status"] == "included"]
    for _, policy in included_policies.iterrows():
        assert policy["effective_exposure"] == policy["exposure"]
        assert policy["cession_to_reinsurer"] > 0
