import pandas as pd
import pytest
from pathlib import Path

from src.loaders import BordereauLoader, BordereauValidationError


def test_aviation_with_hull_limit():
    """
    Test: Bordereau aviation avec colonne 'hull_limit' doit être accepté et mappé vers 'exposure'
    
    CONTEXTE:
    - Line of business: aviation (détectée depuis le path)
    - Colonne d'exposition: hull_limit
    
    COMPORTEMENT ATTENDU:
    - Le bordereau est chargé avec succès
    - La colonne 'hull_limit' est renommée en 'exposure'
    """
    test_data = pd.DataFrame({
        "policy_id": ["POL-001"],
        "INSURED_NAME": ["COMPANY A"],
        "hull_limit": [1_000_000],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2024-12-31"],
        "line_of_business": ["aviation"],
    })
    
    test_file = Path("/tmp/bordereaux/aviation/test_aviation.csv")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_data.to_csv(test_file, index=False)
    
    loader = BordereauLoader(test_file)
    df = loader.load()
    
    assert "exposure" in df.columns
    assert "hull_limit" not in df.columns
    assert df["exposure"].iloc[0] == 1_000_000


def test_aviation_with_liab_limit():
    """
    Test: Bordereau aviation avec colonne 'liab_limit' doit être accepté et mappé vers 'exposure'
    
    CONTEXTE:
    - Line of business: aviation (détectée depuis le path)
    - Colonne d'exposition: liab_limit
    
    COMPORTEMENT ATTENDU:
    - Le bordereau est chargé avec succès
    - La colonne 'liab_limit' est renommée en 'exposure'
    """
    test_data = pd.DataFrame({
        "policy_id": ["POL-001"],
        "INSURED_NAME": ["COMPANY A"],
        "liab_limit": [500_000],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2024-12-31"],
        "line_of_business": ["aviation"],
    })
    
    test_file = Path("/tmp/bordereaux/aviation/test_aviation_liab.csv")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_data.to_csv(test_file, index=False)
    
    loader = BordereauLoader(test_file)
    df = loader.load()
    
    assert "exposure" in df.columns
    assert "liab_limit" not in df.columns
    assert df["exposure"].iloc[0] == 500_000


def test_aviation_without_valid_exposure_column_fails():
    """
    Test: Bordereau aviation sans colonne d'exposition valide doit être rejeté
    
    CONTEXTE:
    - Line of business: aviation (détectée depuis le path)
    - Colonne d'exposition: 'exposure' (générique, pas acceptée pour aviation)
    
    COMPORTEMENT ATTENDU:
    - Le chargement échoue avec BordereauValidationError
    - Le message d'erreur indique les colonnes attendues: hull_limit, liab_limit
    """
    test_data = pd.DataFrame({
        "policy_id": ["POL-001"],
        "INSURED_NAME": ["COMPANY A"],
        "exposure": [1_000_000],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2024-12-31"],
        "line_of_business": ["aviation"],
    })
    
    test_file = Path("/tmp/bordereaux/aviation/test_aviation_invalid.csv")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_data.to_csv(test_file, index=False)
    
    loader = BordereauLoader(test_file)
    
    with pytest.raises(BordereauValidationError) as exc_info:
        loader.load()
    
    error_message = str(exc_info.value)
    assert "hull_limit" in error_message
    assert "liab_limit" in error_message
    assert "aviation" in error_message.lower()


def test_casualty_with_limit():
    """
    Test: Bordereau casualty avec colonne 'limit' doit être accepté et mappé vers 'exposure'
    
    CONTEXTE:
    - Line of business: casualty (détectée depuis le path)
    - Colonne d'exposition: limit
    
    COMPORTEMENT ATTENDU:
    - Le bordereau est chargé avec succès
    - La colonne 'limit' est renommée en 'exposure'
    """
    test_data = pd.DataFrame({
        "policy_id": ["POL-001"],
        "INSURED_NAME": ["COMPANY A"],
        "limit": [2_000_000],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2024-12-31"],
        "line_of_business": ["casualty"],
    })
    
    test_file = Path("/tmp/bordereaux/casualty/test_casualty.csv")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_data.to_csv(test_file, index=False)
    
    loader = BordereauLoader(test_file)
    df = loader.load()
    
    assert "exposure" in df.columns
    assert "limit" not in df.columns
    assert df["exposure"].iloc[0] == 2_000_000


def test_casualty_without_valid_exposure_column_fails():
    """
    Test: Bordereau casualty sans colonne 'limit' doit être rejeté
    
    CONTEXTE:
    - Line of business: casualty (détectée depuis le path)
    - Colonne d'exposition: 'exposure' (générique, pas acceptée pour casualty)
    
    COMPORTEMENT ATTENDU:
    - Le chargement échoue avec BordereauValidationError
    - Le message d'erreur indique la colonne attendue: limit
    """
    test_data = pd.DataFrame({
        "policy_id": ["POL-001"],
        "INSURED_NAME": ["COMPANY A"],
        "exposure": [2_000_000],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2024-12-31"],
        "line_of_business": ["casualty"],
    })
    
    test_file = Path("/tmp/bordereaux/casualty/test_casualty_invalid.csv")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_data.to_csv(test_file, index=False)
    
    loader = BordereauLoader(test_file)
    
    with pytest.raises(BordereauValidationError) as exc_info:
        loader.load()
    
    error_message = str(exc_info.value)
    assert "limit" in error_message
    assert "casualty" in error_message.lower()


def test_test_lob_with_exposure():
    """
    Test: Bordereau 'test' avec colonne 'exposure' doit être accepté
    
    CONTEXTE:
    - Line of business: test
    - Colonne d'exposition: exposure
    
    COMPORTEMENT ATTENDU:
    - Le bordereau est chargé avec succès
    - La colonne 'exposure' reste inchangée
    """
    test_data = pd.DataFrame({
        "policy_id": ["POL-001"],
        "INSURED_NAME": ["COMPANY A"],
        "exposure": [1_000_000],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2024-12-31"],
        "line_of_business": ["test"],
    })
    
    test_file = Path("/tmp/test_test.csv")
    test_data.to_csv(test_file, index=False)
    
    loader = BordereauLoader(test_file, line_of_business="test")
    df = loader.load()
    
    assert "exposure" in df.columns
    assert df["exposure"].iloc[0] == 1_000_000


def test_unknown_line_of_business_fails():
    """
    Test: Line of business inconnue doit être rejetée
    
    CONTEXTE:
    - Line of business: property (non supportée)
    - Colonne d'exposition: exposure
    
    COMPORTEMENT ATTENDU:
    - Le chargement échoue avec BordereauValidationError
    - Le message d'erreur liste les lignes de business supportées
    """
    test_data = pd.DataFrame({
        "policy_id": ["POL-001"],
        "INSURED_NAME": ["COMPANY A"],
        "exposure": [1_000_000],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2024-12-31"],
        "line_of_business": ["property"],
    })
    
    test_file = Path("/tmp/bordereaux/property/test_property.csv")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_data.to_csv(test_file, index=False)
    
    loader = BordereauLoader(test_file)
    
    with pytest.raises(BordereauValidationError) as exc_info:
        loader.load()
    
    error_message = str(exc_info.value)
    assert "property" in error_message.lower()
    assert "aviation" in error_message
    assert "casualty" in error_message
    assert "test" in error_message


def test_no_line_of_business_fails():
    """
    Test: Bordereau sans ligne de business spécifiée doit être rejeté
    
    CONTEXTE:
    - Line of business: None (non détectée)
    - Colonne d'exposition: exposure
    
    COMPORTEMENT ATTENDU:
    - Le chargement échoue avec BordereauValidationError
    - Le message d'erreur demande de spécifier la ligne de business
    """
    test_data = pd.DataFrame({
        "policy_id": ["POL-001"],
        "INSURED_NAME": ["COMPANY A"],
        "exposure": [1_000_000],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2024-12-31"],
        "line_of_business": ["generic"],
    })
    
    test_file = Path("/tmp/test_generic.csv")
    test_data.to_csv(test_file, index=False)
    
    loader = BordereauLoader(test_file, line_of_business=None)
    
    with pytest.raises(BordereauValidationError) as exc_info:
        loader.load()
    
    error_message = str(exc_info.value)
    assert "required" in error_message.lower()
    assert "line of business" in error_message.lower()

