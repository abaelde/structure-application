import pandas as pd
import argparse
import sys
from pathlib import Path
from datetime import datetime
from src.domain.bordereau import Bordereau
from src.managers import ProgramManager
from src.engine import apply_program_to_bordereau
from src.presentation import generate_detailed_report


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

    print("1. Loading and validating bordereau...")
    bordereau_df = Bordereau.from_csv(args.bordereau)
    print(f"   ✓ Bordereau loaded successfully: {len(bordereau_df)} policies")
    print()

    print("2. Loading program configuration...")
    manager = ProgramManager(backend="excel")
    program = manager.load(args.program)
    print(f"   ✓ Program loaded: {program.name}")
    print(f"   ✓ Number of structures: {len(program.structures)}")
    print()

    print("3. Program configuration:")
    print("-" * 80)
    program.describe()
    print()

    print("4. Applying program to bordereau...")
    calculation_date = "2024-06-01"  # Date de calcul par défaut
    bordereau_with_net, results = apply_program_to_bordereau(
        bordereau_df, program, calculation_date
    )
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
