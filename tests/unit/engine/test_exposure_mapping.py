import pandas as pd
import pytest
from src.engine import apply_program_to_bordereau
from src.engine.exposure_validation import ExposureValidationError
from tests.builders import build_program, build_quota_share


def test_exposure_mapping_success_aviation():
    """
    Test : Calcul d'exposition aviation avec HULL et LIABILITY pour un programme aviation
    
    PROGRAMME:
    - Underwriting department: aviation
    - Structure: Quota Share 30%
    
    BORDEREAU:
    - Colonnes d'exposition: HULL_LIMIT, LIABILITY_LIMIT, HULL_SHARE, LIABILITY_SHARE
    - Exposition calculée = (HULL_LIMIT × HULL_SHARE) + (LIABILITY_LIMIT × LIABILITY_SHARE)
    
    RÉSULTAT ATTENDU:
    - L'exposition est calculée correctement
    - Le traitement se déroule sans erreur
    - La cession est calculée sur l'exposition totale
    """
    qs = build_quota_share(
        name="QS_30",
        sections_config=[{
            "cession_pct": 0.30,
            "signed_share": 1.0,
            "includes_hull": True,
            "includes_liability": True,
        }]
    )
    program = build_program(
        name="TEST_AVIATION",
        structures=[qs],
        underwriting_department="aviation"
    )
    
    bordereau_df = pd.DataFrame({
        "INSURED_NAME": ["TEST COMPANY"],
        "HULL_LIMIT": [10_000_000],
        "LIABILITY_LIMIT": [50_000_000],
        "HULL_SHARE": [0.20],
        "LIABILITY_SHARE": [0.10],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2025-01-01"],
    })
    
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau_df, program, calculation_date=calculation_date
    )
    
    expected_exposure = (10_000_000 * 0.20) + (50_000_000 * 0.10)
    assert results_df["exposure"].iloc[0] == expected_exposure
    assert abs(results_df["cession_to_reinsurer"].iloc[0] - (expected_exposure * 0.30)) < 1


def test_exposure_mapping_failure_wrong_column():
    """
    Test : Erreur levée quand le bordereau n'a pas les colonnes d'exposition aviation requises
    
    PROGRAMME:
    - Underwriting department: aviation
    - Attend: Au moins HULL_LIMIT ou LIABILITY_LIMIT (avec leur SHARE correspondant)
    
    BORDEREAU:
    - Colonne d'exposition: LIMIT (valide pour casualty, pas aviation)
    
    RÉSULTAT ATTENDU:
    - ExposureMappingError est levée
    - Le message d'erreur indique qu'il faut au moins une exposition aviation
    """
    qs = build_quota_share(
        name="QS_30",
        sections_config=[{
            "cession_pct": 0.30,
            "signed_share": 1.0,
            "includes_hull": True,
            "includes_liability": True,
        }]
    )
    program = build_program(
        name="TEST_AVIATION",
        structures=[qs],
        underwriting_department="aviation"
    )
    
    bordereau_df = pd.DataFrame({
        "INSURED_NAME": ["TEST COMPANY"],
        "LIMIT": [1_000_000],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2025-01-01"],
    })
    
    with pytest.raises(ExposureValidationError) as exc_info:
        apply_program_to_bordereau(bordereau_df, program)
    
    error_message = str(exc_info.value)
    assert "at least one exposure type" in error_message.lower()
    assert "HULL_LIMIT" in error_message
    assert "LIABILITY_LIMIT" in error_message
    assert "aviation" in error_message.lower()

