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
        df = load_bordereau("examples/bordereaux/aviation/bordereau_aviation_axa_xl.csv")
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
        "policy_id": ["POL-001", "POL-002", "POL-001"],
        "INSURED_NAME": ["COMPANY A", "COMPANY B", "COMPANY C"],
        "BUSCL_COUNTRY_CD": ["US", "FR", "UK"],
        "BUSCL_REGION": ["NA", "EU", "EU"],
        "BUSCL_LIMIT_CURRENCY_CD": ["USD", "EUR", "GBP"],
        "line_of_business": ["Aviation", "Property", "Aviation"],
        "exposition": [0, 25.5, 30.0],
        "INCEPTION_DT": ["2024-01-01", "2024-02-01", "2024-03-01"],
        "EXPIRE_DT": ["2024-12-31", "2025-01-31", "2025-02-28"],
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
        "policy_id": ["POL-001", "POL-002", "POL-003"],
        "INSURED_NAME": ["COMPANY A", "COMPANY B", "COMPANY C"],
        "BUSCL_LIMIT_CURRENCY_CD": ["USD", "EUR", "GBP"],
        "line_of_business": ["Test", "Test", "Test"],
        "exposition": ["abc", -50, 25.5],
        "INCEPTION_DT": ["2024-01-01", "invalid-date", "2024-03-01"],
        "EXPIRE_DT": ["2024-12-31", "2024-12-31", "2023-12-31"],
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


def test_missing_required_columns():
    print("=" * 80)
    print("TEST 4: Missing Required Columns")
    print("=" * 80)
    
    test_data = pd.DataFrame({
        "policy_id": ["POL-001", "POL-002"],
        "INSURED_NAME": ["COMPANY A", "COMPANY B"],
        "INCEPTION_DT": ["2024-01-01", "2024-02-01"],
        "EXPIRE_DT": ["2024-12-31", "2025-01-31"],
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


def test_unknown_columns():
    print("=" * 80)
    print("TEST 5: Unknown Columns (should fail)")
    print("=" * 80)
    
    test_data = pd.DataFrame({
        "policy_id": ["POL-001", "POL-002"],
        "INSURED_NAME": ["COMPANY A", "COMPANY B"],
        "line_of_business": ["Test", "Test"],
        "exposition": [25.5, 30.0],
        "INCEPTION_DT": ["2024-01-01", "2024-02-01"],
        "EXPIRE_DT": ["2024-12-31", "2025-01-31"],
        "unknown_column": ["value1", "value2"],
        "another_bad_column": ["x", "y"],
    })
    
    test_file = "/tmp/test_unknown.csv"
    test_data.to_csv(test_file, index=False)
    
    try:
        df = load_bordereau(test_file)
        print(f"✗ Unexpected: Loaded {len(df)} policies (should have failed)")
    except BordereauValidationError as e:
        print(f"✓ Expected failure:")
        print(str(e))
    print()


def test_only_required_columns():
    print("=" * 80)
    print("TEST 6: Only Required Columns (should pass)")
    print("=" * 80)
    
    test_data = pd.DataFrame({
        "policy_id": ["POL-001", "POL-002"],
        "INSURED_NAME": ["COMPANY A", "COMPANY B"],
        "line_of_business": ["Test", "Test"],
        "exposition": [25.5, 30.0],
        "INCEPTION_DT": ["2024-01-01", "2024-02-01"],
        "EXPIRE_DT": ["2024-12-31", "2025-01-31"],
    })
    
    test_file = "/tmp/test_only_req.csv"
    test_data.to_csv(test_file, index=False)
    
    try:
        df = load_bordereau(test_file)
        print(f"✓ Success: Loaded {len(df)} policies (dimension columns are optional)")
    except BordereauValidationError as e:
        print(f"✗ Unexpected failure: {e}")
    print()


def test_partial_dimensions():
    print("=" * 80)
    print("TEST 7: Partial Dimension Columns (should pass)")
    print("=" * 80)
    
    test_data = pd.DataFrame({
        "policy_id": ["POL-001", "POL-002"],
        "INSURED_NAME": ["COMPANY A", "COMPANY B"],
        "exposition": [25.5, 30.0],
        "INCEPTION_DT": ["2024-01-01", "2024-02-01"],
        "EXPIRE_DT": ["2024-12-31", "2025-01-31"],
        "BUSCL_LIMIT_CURRENCY_CD": ["USD", "EUR"],
        "line_of_business": ["Aviation", "Property"],
    })
    
    test_file = "/tmp/test_partial_dim.csv"
    test_data.to_csv(test_file, index=False)
    
    try:
        df = load_bordereau(test_file)
        print(f"✓ Success: Loaded {len(df)} policies (can have some dimension columns)")
    except BordereauValidationError as e:
        print(f"✗ Unexpected failure: {e}")
    print()


def test_null_dimension_columns():
    print("=" * 80)
    print("TEST 8: Null Values in Dimension Columns (should pass)")
    print("=" * 80)
    
    test_data = pd.DataFrame({
        "policy_id": ["POL-001", "POL-002"],
        "INSURED_NAME": ["COMPANY A", "COMPANY B"],
        "BUSCL_COUNTRY_CD": [None, "US"],
        "BUSCL_LIMIT_CURRENCY_CD": [None, "USD"],
        "line_of_business": ["Test", "Test"],
        "exposition": [25.5, 30.0],
        "INCEPTION_DT": ["2024-01-01", "2024-02-01"],
        "EXPIRE_DT": ["2024-12-31", "2025-01-31"],
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
    print("TEST 9: Null Values in Required Columns (should fail)")
    print("=" * 80)
    
    test_data = pd.DataFrame({
        "policy_id": ["POL-001", None, "POL-003"],
        "INSURED_NAME": [None, "COMPANY B", "COMPANY C"],
        "line_of_business": ["Test", "Test", "Test"],
        "exposition": [25.5, None, 30.0],
        "INCEPTION_DT": ["2024-01-01", "2024-02-01", None],
        "EXPIRE_DT": ["2024-12-31", None, "2025-02-28"],
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
    test_missing_required_columns()
    test_unknown_columns()
    test_only_required_columns()
    test_partial_dimensions()
    test_null_dimension_columns()
    test_null_required_columns()
    
    print("=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()

