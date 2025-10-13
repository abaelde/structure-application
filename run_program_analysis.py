import pandas as pd
import argparse
import sys
from pathlib import Path
from datetime import datetime
from src.loaders import (
    ProgramLoader,
    load_bordereau,
    BordereauValidationError,
)
from src.engine import apply_program_to_bordereau
from src.presentation import display_program, generate_detailed_report


def main():
    parser = argparse.ArgumentParser(
        description="Apply reinsurance program to bordereau and generate analysis reports"
    )
    parser.add_argument(
        "--program", "-p", required=True, help="Path to the program Excel file"
    )
    parser.add_argument(
        "--bordereau", "-b", required=True, help="Path to the bordereau CSV file"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="output",
        help="Output directory for results (default: output/)",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("REINSURANCE PROGRAM ANALYSIS")
    print("=" * 80)
    print()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    program_name = Path(args.program).stem
    bordereau_name = Path(args.bordereau).stem

    analysis_subdir = output_dir / f"{program_name}_{bordereau_name}_{timestamp}"
    analysis_subdir.mkdir(exist_ok=True)

    print(f"📁 Output directory: {analysis_subdir}")
    print()

    try:
        print("1. Loading and validating bordereau...")
        bordereau_df = load_bordereau(args.bordereau)
        print(f"   ✓ Bordereau loaded successfully: {len(bordereau_df)} policies")
        print()

        print("2. Loading program configuration...")
        loader = ProgramLoader(args.program)
        program = loader.get_program()
        print(f"   ✓ Program loaded: {program['name']}")
        print(f"   ✓ Number of structures: {len(program['structures'])}")
        print()

    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        sys.exit(1)
    except BordereauValidationError as e:
        print(f"❌ Error: Bordereau validation failed:\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading files: {e}")
        sys.exit(1)

    print("3. Program configuration:")
    print("-" * 80)
    display_program(program)
    print()

    print("4. Applying program to bordereau...")
    bordereau_with_net, results = apply_program_to_bordereau(bordereau_df, program)
    print(f"   ✓ Program applied to {len(results)} policies")
    print()

    print("5. Saving results...")

    output_bordereau_file = analysis_subdir / "bordereau_with_cession.csv"
    bordereau_with_net.to_csv(output_bordereau_file, index=False)
    print(f"   ✓ Bordereau with cessions: {output_bordereau_file}")

    detailed_report_file = analysis_subdir / "detailed_report.txt"
    generate_detailed_report(results, program, str(detailed_report_file))
    print()

    print("=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nAll results saved in: {analysis_subdir}")


if __name__ == "__main__":
    main()

