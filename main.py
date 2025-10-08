import pandas as pd
import argparse
import sys
from structures import (
    ProgramLoader,
    load_bordereau,
    BordereauValidationError,
    apply_program_to_bordereau,
    generate_detailed_report,
    write_detailed_results,
)
from structures.program_display import display_program


def main():
    parser = argparse.ArgumentParser(
        description="Reinsurance Program Application System"
    )
    parser.add_argument(
        "--program", "-p", required=True, help="Path to the program Excel file"
    )
    parser.add_argument(
        "--bordereau", "-b", required=True, help="Path to the bordereau CSV file"
    )

    args = parser.parse_args()

    print("=== Reinsurance Program Application System ===\n")

    try:
        print("Loading and validating bordereau...")
        bordereau_df = load_bordereau(args.bordereau)
        print(f"✓ Bordereau loaded successfully: {len(bordereau_df)} policies")
        print(bordereau_df)
        print()

        loader = ProgramLoader(args.program)
        program = loader.get_program()
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except BordereauValidationError as e:
        print(f"Error: Bordereau validation failed:\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading files: {e}")
        sys.exit(1)

    display_program(program)

    bordereau_with_net, results = apply_program_to_bordereau(bordereau_df, program)

    print("\n\n" + "=" * 80)
    print("BORDEREAU WITH CESSION TO REINSURER")
    print("=" * 80)
    print(bordereau_with_net)

    print("\n\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(
        results[["insured_name", "exposure", "cession_to_layer_100pct", "cession_to_reinsurer", "retained_by_cedant"]]
    )

    print("\n")
    write_detailed_results(results, program["dimension_columns"])

    generate_detailed_report(results, program, "detailed_report.txt")

    output_bordereau_file = "bordereau_with_cession_to_reinsurer.csv"
    bordereau_with_net.to_csv(output_bordereau_file, index=False)
    print(f"\n✓ Bordereau with Cession to Reinsurer saved: {output_bordereau_file}")


if __name__ == "__main__":
    main()
