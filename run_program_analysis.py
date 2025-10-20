import pandas as pd
import argparse
import sys
from pathlib import Path
from datetime import datetime
from src.managers import ProgramManager, BordereauManager, RunManager
from src.serialization.run_serializer import RunMeta
from src.engine import apply_program_to_bordereau
from src.presentation import generate_detailed_report


def main():
    parser = argparse.ArgumentParser(
        description="Apply reinsurance program to bordereau and generate analysis reports"
    )
    parser.add_argument(
        "--program", "-p", required=True, help="Path to the program CSV folder"
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

    # 1. Charger d'abord le programme (on en a besoin pour valider le bordereau)
    print("1. Loading program configuration...")
    started_at = datetime.now().isoformat()
    p_backend = ProgramManager.detect_backend(args.program)
    p_manager = ProgramManager(backend=p_backend)
    program = p_manager.load(args.program)
    print(f"   ✓ Program loaded: {program.name}")
    print(f"   ✓ Number of structures: {len(program.structures)}\n")

    # 2. Charger + valider le bordereau via le manager (backend auto)
    print("2. Loading and validating bordereau...")
    b_backend = BordereauManager.detect_backend(args.bordereau)
    b_manager = BordereauManager(backend=b_backend)
    bordereau = b_manager.load(args.bordereau, program=program, validate=True)
    print(f"   ✓ Bordereau loaded successfully: {len(bordereau)} policies\n")

    # 3. Program configuration
    print("3. Program configuration:")
    print("-" * 80)
    program.describe()
    print()

    # 4. Application inchangée
    print("4. Applying program to bordereau...")
    calculation_date = "2024-06-01"  # Date de calcul par défaut
    bordereau_with_net, results = apply_program_to_bordereau(
        bordereau, program, calculation_date
    )
    print(f"   ✓ Program applied to {len(results)} policies")
    print()

    # 5. Sauvegarde identique
    print("5. Saving results...")
    output_bordereau_file = analysis_subdir / "bordereau_with_cession.csv"
    bordereau_with_net.to_csv(output_bordereau_file, index=False)
    print(f"   ✓ Bordereau with cessions: {output_bordereau_file}")

    detailed_report_file = analysis_subdir / "detailed_report.txt"
    generate_detailed_report(results, program, str(detailed_report_file))
    print(f"   ✓ Detailed report: {detailed_report_file}")

    # 6. Persistance du Run en CSV (3 tables)
    print("6. Persisting run (CSV)...")
    ended_at = datetime.now().isoformat()

    run_id = f"{program_name}_{bordereau_name}_{timestamp}"  # lisible & unique (ou utilise uuid)
    run_meta = RunMeta(
        run_id=run_id,
        program_name=program.name,
        uw_dept=program.underwriting_department,
        calculation_date=calculation_date,
        source_program=args.program,
        source_bordereau=args.bordereau,
        program_fingerprint=None,  # tu peux injecter un hash du programme si tu veux
        started_at=started_at,
        ended_at=ended_at,
        notes=None,
    )

    r_backend = RunManager.detect_backend(str(analysis_subdir))  # "csv"
    r_manager = RunManager(backend=r_backend)
    # on passe aussi le DF du bordereau pour extraire un éventuel policy_id
    dfs = r_manager.save(
        run_meta,
        results_df=results,
        dest=str(analysis_subdir),
        source_policy_df=bordereau.to_engine_dataframe(),
    )

    print(f"   ✓ Runs CSV: {analysis_subdir / 'runs.csv'}")
    print(f"   ✓ Policies CSV: {analysis_subdir / 'run_policies.csv'}")
    print(f"   ✓ Structures CSV: {analysis_subdir / 'run_policy_structures.csv'}")
    print()

    print("=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nAll results saved in: {analysis_subdir}")


if __name__ == "__main__":
    main()
