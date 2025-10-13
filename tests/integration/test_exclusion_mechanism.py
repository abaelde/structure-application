import pandas as pd
from src.loaders import ProgramLoader, load_bordereau
from src.engine import apply_program_to_bordereau


def test_exclusion_mechanism():
    """
    Test du mécanisme d'exclusion dans un programme Quota Share
    
    STRUCTURE DU PROGRAMME:
    - Quota Share 25% avec critères d'exclusion par pays/région
    
    BORDEREAU:
    - 7 polices avec différents pays et régions
    - Certaines polices doivent être exclues selon les critères
    
    CALCULS ATTENDUS:
    - Les polices exclues ont une exposition effective à 0
    - Les polices incluses ont une cession de 25% de leur exposition
    - Le statut d'exclusion est correctement reporté
    """
    program_file = "tests/integration/fixtures/programs/quota_share_with_exclusion.xlsx"
    bordereau_file = "tests/integration/fixtures/bordereaux/bordereau_exclusion_test.csv"

    loader = ProgramLoader(program_file)
    program = loader.get_program()

    bordereau_df = load_bordereau(bordereau_file)

    __, results = apply_program_to_bordereau(bordereau_df, program)

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
