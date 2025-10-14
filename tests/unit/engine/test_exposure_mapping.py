import pandas as pd
import pytest
from src.engine import apply_program_to_bordereau
from src.loaders.exposure_mapping import ExposureMappingError
from tests.builders import build_program, build_quota_share


def test_exposure_mapping_success_aviation():
    """
    Test : Mapping réussi d'une colonne HULL_LIMIT vers exposure pour un programme aviation
    
    PROGRAMME:
    - Underwriting department: aviation
    - Structure: Quota Share 30%
    
    BORDEREAU:
    - Colonne d'exposition: HULL_LIMIT (valide pour aviation)
    
    RÉSULTAT ATTENDU:
    - HULL_LIMIT est mappée vers exposure
    - Le traitement se déroule sans erreur
    - La cession est calculée correctement
    """
    qs = build_quota_share(name="QS_30", cession_pct=0.30, signed_share=1.0)
    program = build_program(
        name="TEST_AVIATION",
        structures=[qs],
        underwriting_department="aviation"
    )
    
    bordereau_df = pd.DataFrame({
        "INSURED_NAME": ["TEST COMPANY"],
        "HULL_LIMIT": [1_000_000],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2025-01-01"],
    })
    
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau_df, program, calculation_date=calculation_date
    )
    
    assert "exposure" in bordereau_with_net.columns
    assert bordereau_with_net["exposure"].iloc[0] == 1_000_000
    assert abs(results_df["cession_to_reinsurer"].iloc[0] - 300_000) < 1


def test_exposure_mapping_failure_wrong_column():
    """
    Test : Erreur levée quand le bordereau n'a pas de colonne d'exposition valide
    
    PROGRAMME:
    - Underwriting department: aviation
    - Attend: HULL_LIMIT ou LIAB_LIMIT
    
    BORDEREAU:
    - Colonne d'exposition: LIMIT (valide pour casualty, pas aviation)
    
    RÉSULTAT ATTENDU:
    - ExposureMappingError est levée
    - Le message d'erreur indique les colonnes attendues
    """
    qs = build_quota_share(name="QS_30", cession_pct=0.30, signed_share=1.0)
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
    
    with pytest.raises(ExposureMappingError) as exc_info:
        apply_program_to_bordereau(bordereau_df, program)
    
    error_message = str(exc_info.value)
    assert "HULL_LIMIT" in error_message
    assert "LIAB_LIMIT" in error_message
    assert "aviation" in error_message.lower()

