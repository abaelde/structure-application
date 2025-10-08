import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from structures import load_bordereau, BordereauLoader, BordereauValidationError


def test_valid_bordereau():
    print("=" * 80)
    print("TEST 1: Valid Bordereau")
    print("=" * 80)
    
    try:
        df = load_bordereau("examples/bordereaux/bordereau_aviation_axa_xl.csv")
        print(f"✓ Success: Loaded {len(df)} policies")
        print(df.head())
    except BordereauValidationError as e:
        print(f"✗ Failed: {e}")
    print()


def test_bordereau_with_warnings():
    print("=" * 80)
    print("TEST 2: Bordereau with Warnings (zero exposition, duplicates)")
    print("=" * 80)
    
    test_data = pd.DataFrame({
        "numero_police": ["POL-001", "POL-002", "POL-001"],
        "nom_assure": ["Company A", "Company B", "Company C"],
        "BUSCL_COUNTRY_CD": ["US", "FR", "UK"],
        "BUSCL_REGION": ["NA", "EU", "EU"],
        "BUSCL_CLASS_OF_BUSINESS_1": [None, None, None],
        "BUSCL_CLASS_OF_BUSINESS_2": [None, None, None],
        "BUSCL_CLASS_OF_BUSINESS_3": [None, None, None],
        "BUSCL_LIMIT_CURRENCY_CD": ["USD", "EUR", "GBP"],
        "line_of_business": ["Aviation", "Property", "Aviation"],
        "industry": ["Transportation", "Construction", "Transportation"],
        "sic_code": ["4512", "1623", "4512"],
        "include": [None, None, None],
        "exposition": [0, 25.5, 30.0],
        "inception_date": ["2024-01-01", "2024-02-01", "2024-03-01"],
        "expiry_date": ["2024-12-31", "2025-01-31", "2025-02-28"],
        "unknown_column": ["value1", "value2", "value3"],
    })
    
    test_file = "/tmp/test_warnings.csv"
    test_data.to_csv(test_file, index=False)
    
    try:
        loader = BordereauLoader(test_file)
        df = loader.load()
        print(f"✓ Success: Loaded {len(df)} policies")
        print(f"Warnings: {len(loader.validation_warnings)}")
        for warning in loader.validation_warnings:
            print(f"  - {warning}")
    except BordereauValidationError as e:
        print(f"✗ Failed: {e}")
    print()


def test_invalid_bordereau():
    print("=" * 80)
    print("TEST 3: Invalid Bordereau (multiple errors)")
    print("=" * 80)
    
    test_data = pd.DataFrame({
        "numero_police": ["POL-001", "POL-002", "POL-003"],
        "nom_assure": ["Company A", "Company B", "Company C"],
        "BUSCL_COUNTRY_CD": ["US", "FR", "UK"],
        "BUSCL_REGION": ["NA", "EU", "EU"],
        "BUSCL_CLASS_OF_BUSINESS_1": [None, None, None],
        "BUSCL_CLASS_OF_BUSINESS_2": [None, None, None],
        "BUSCL_CLASS_OF_BUSINESS_3": [None, None, None],
        "BUSCL_LIMIT_CURRENCY_CD": ["USD", "EUR", "GBP"],
        "line_of_business": ["Aviation", "Property", "Aviation"],
        "industry": ["Transportation", "Construction", "Transportation"],
        "sic_code": ["4512", "1623", "4512"],
        "include": [None, None, None],
        "exposition": ["abc", -50, 25.5],
        "inception_date": ["2024-01-01", "invalid-date", "2024-03-01"],
        "expiry_date": ["2024-12-31", "2024-12-31", "2023-12-31"],
    })
    
    test_file = "/tmp/test_invalid.csv"
    test_data.to_csv(test_file, index=False)
    
    try:
        df = load_bordereau(test_file)
        print(f"✗ Unexpected: Loaded {len(df)} policies (should have failed)")
    except BordereauValidationError as e:
        print(f"✓ Expected failure:")
        print(str(e))
    print()


def test_missing_columns():
    print("=" * 80)
    print("TEST 4: Missing Mandatory Columns")
    print("=" * 80)
    
    test_data = pd.DataFrame({
        "numero_police": ["POL-001", "POL-002"],
        "nom_assure": ["Company A", "Company B"],
        "exposition": [25.5, 30.0],
        "inception_date": ["2024-01-01", "2024-02-01"],
        "expiry_date": ["2024-12-31", "2025-01-31"],
    })
    
    test_file = "/tmp/test_missing.csv"
    test_data.to_csv(test_file, index=False)
    
    try:
        df = load_bordereau(test_file)
        print(f"✗ Unexpected: Loaded {len(df)} policies (should have failed)")
    except BordereauValidationError as e:
        print(f"✓ Expected failure:")
        print(str(e))
    print()


def test_null_dimension_columns():
    print("=" * 80)
    print("TEST 5: Null Values in Dimension Columns (should pass)")
    print("=" * 80)
    
    test_data = pd.DataFrame({
        "numero_police": ["POL-001", "POL-002"],
        "nom_assure": ["Company A", "Company B"],
        "BUSCL_COUNTRY_CD": [None, "US"],
        "BUSCL_REGION": [None, None],
        "BUSCL_CLASS_OF_BUSINESS_1": [None, None],
        "BUSCL_CLASS_OF_BUSINESS_2": [None, None],
        "BUSCL_CLASS_OF_BUSINESS_3": [None, None],
        "BUSCL_LIMIT_CURRENCY_CD": [None, "USD"],
        "line_of_business": [None, "Aviation"],
        "industry": [None, "Transportation"],
        "sic_code": [None, "4512"],
        "include": [None, None],
        "exposition": [25.5, 30.0],
        "inception_date": ["2024-01-01", "2024-02-01"],
        "expiry_date": ["2024-12-31", "2025-01-31"],
    })
    
    test_file = "/tmp/test_null_dim.csv"
    test_data.to_csv(test_file, index=False)
    
    try:
        df = load_bordereau(test_file)
        print(f"✓ Success: Loaded {len(df)} policies (dimension columns can be null)")
    except BordereauValidationError as e:
        print(f"✗ Unexpected failure: {e}")
    print()


def test_null_required_columns():
    print("=" * 80)
    print("TEST 6: Null Values in Required Columns (should fail)")
    print("=" * 80)
    
    test_data = pd.DataFrame({
        "numero_police": ["POL-001", None, "POL-003"],
        "nom_assure": [None, "Company B", "Company C"],
        "BUSCL_COUNTRY_CD": [None, None, None],
        "BUSCL_REGION": [None, None, None],
        "BUSCL_CLASS_OF_BUSINESS_1": [None, None, None],
        "BUSCL_CLASS_OF_BUSINESS_2": [None, None, None],
        "BUSCL_CLASS_OF_BUSINESS_3": [None, None, None],
        "BUSCL_LIMIT_CURRENCY_CD": [None, None, None],
        "line_of_business": [None, None, None],
        "industry": [None, None, None],
        "sic_code": [None, None, None],
        "include": [None, None, None],
        "exposition": [25.5, None, 30.0],
        "inception_date": ["2024-01-01", "2024-02-01", None],
        "expiry_date": ["2024-12-31", None, "2025-02-28"],
    })
    
    test_file = "/tmp/test_null_req.csv"
    test_data.to_csv(test_file, index=False)
    
    try:
        df = load_bordereau(test_file)
        print(f"✗ Unexpected: Loaded {len(df)} policies (should have failed)")
    except BordereauValidationError as e:
        print(f"✓ Expected failure:")
        print(str(e))
    print()


def main():
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "BORDEREAU VALIDATION TEST SUITE" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    test_valid_bordereau()
    test_bordereau_with_warnings()
    test_invalid_bordereau()
    test_missing_columns()
    test_null_dimension_columns()
    test_null_required_columns()
    
    print("=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()

