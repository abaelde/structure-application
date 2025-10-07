import pandas as pd
import argparse
import sys
from structures import (
    ProgramLoader,
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
        bordereau_df = pd.read_csv(args.bordereau)
        print("Bordereau loaded:")
        print(bordereau_df)
        print()

        loader = ProgramLoader(args.program)
        program = loader.get_program()
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading files: {e}")
        sys.exit(1)

    display_program(program)

    bordereau_with_net, results = apply_program_to_bordereau(bordereau_df, program)

    print("\n\n" + "=" * 80)
    print("BORDEREAU WITH NET EXPOSURE")
    print("=" * 80)
    print(bordereau_with_net)

    print("\n\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(
        results[["policy_number", "exposure", "gross_ceded", "net_ceded", "retained"]]
    )

    print("\n")
    write_detailed_results(results, program["dimension_columns"])

    generate_detailed_report(results, program, "detailed_report.txt")

    output_bordereau_file = "bordereau_with_net_exposure.csv"
    bordereau_with_net.to_csv(output_bordereau_file, index=False)
    print(f"\n✓ Bordereau with Net Exposure saved: {output_bordereau_file}")


if __name__ == "__main__":
    main()
