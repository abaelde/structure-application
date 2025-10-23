import pandas as pd
import argparse
import sys
from pathlib import Path
from datetime import datetime
from src.managers import ProgramManager, BordereauManager, RunManager
from src.serialization.run_serializer import RunMeta
from src.engine import apply_program_to_bordereau, apply_program_to_bordereau_simple
from src.presentation import generate_detailed_report
from snowflake_utils import SnowflakeConfig, get_snowpark_session, close_snowpark_session
from src.managers.program_snowpark_manager import SnowparkProgramManager

def main():
    parser = argparse.ArgumentParser(
        description="Apply reinsurance program to bordereau and generate analysis reports",
        epilog="""
Examples:
  # Load program from Snowflake by ID via Snowpark
  python run_program_analysis.py --program-id 1 -b bordereau.csv
  
  # Load program from Snowflake by ID via Snowpark with simplified export
  python run_program_analysis.py --program-id 1 -b bordereau.csv --simple
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
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
    parser.add_argument(
        "--simple",
        "-s",
        action="store_true",
        help="Use simplified export (exposure per policy only)",
    )
    parser.add_argument(
        "--program-id",
        type=int,
        required=True,
        help="Load program by ID from Snowflake via Snowpark",
    )

    args = parser.parse_args()


    print("=" * 80)
    print("REINSURANCE PROGRAM ANALYSIS")
    print("=" * 80)
    print()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Nom du programme basé sur l'ID
    program_name = f"program_id_{args.program_id}"
    
    bordereau_name = Path(args.bordereau).stem

    analysis_subdir = output_dir / f"{program_name}_{bordereau_name}_{timestamp}"
    analysis_subdir.mkdir(exist_ok=True)

    print(f"📁 Output directory: {analysis_subdir}")
    print()

    # 1. Charger le programme depuis Snowflake par ID via Snowpark
    print("1. Loading program configuration via Snowpark...")
    started_at = datetime.now().isoformat()
    
    try:
        print(f"   🔍 Loading program by ID: {args.program_id}")
        config = SnowflakeConfig.load()
        if not config.validate():
            print(f"   ❌ Invalid Snowflake configuration")
            sys.exit(1)
        
        # Obtenir une session Snowpark
        session = get_snowpark_session()
        
        try:
            p_manager = SnowparkProgramManager(session)
            program = p_manager.load(args.program_id)
            print(f"   ✓ Program loaded via Snowpark: {program.name}")
            
        finally:
            # Fermer la session Snowpark
            close_snowpark_session()
        
    except Exception as e:
        print(f"   ❌ Failed to load program by ID {args.program_id} via Snowpark: {e}")
        sys.exit(1)
    
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

    # 4. Application du programme
    print("4. Applying program to bordereau...")
    calculation_date = "2024-06-01"  # Date de calcul par défaut

    if args.simple:
        print("   📊 Using simplified export (exposure per policy only)")
        results = apply_program_to_bordereau_simple(
            bordereau, program, calculation_date
        )
        print(f"   ✓ Program applied to {len(results)} policies (simplified)")
    else:
        print("   📊 Using detailed export (full structure details)")
        bordereau_with_net, results = apply_program_to_bordereau(
            bordereau, program, calculation_date
        )
        print(f"   ✓ Program applied to {len(results)} policies (detailed)")
    print()

    # 5. Sauvegarde des résultats
    print("5. Saving results...")

    if args.simple:
        # Export simplifié
        simple_results_file = analysis_subdir / "simple_results.csv"
        results.to_csv(simple_results_file, index=False)
        print(f"   ✓ Simple results: {simple_results_file}")
    else:
        # Export détaillé (legacy)
        output_bordereau_file = analysis_subdir / "bordereau_with_cession.csv"
        bordereau_with_net.to_csv(output_bordereau_file, index=False)
        print(f"   ✓ Bordereau with cessions: {output_bordereau_file}")

        detailed_report_file = analysis_subdir / "detailed_report.txt"
        generate_detailed_report(results, program, str(detailed_report_file))
        print(f"   ✓ Detailed report: {detailed_report_file}")

    # 6. Persistance du Run en CSV (3 tables) - seulement pour l'export détaillé
    if not args.simple:
        print("6. Persisting run (CSV)...")
        ended_at = datetime.now().isoformat()

        run_id = f"{program_name}_{bordereau_name}_{timestamp}"  # lisible & unique (ou utilise uuid)
        # Source du programme pour les métadonnées
        source_program = f"snowflake://program_id={args.program_id}"

        run_meta = RunMeta(
            run_id=run_id,
            program_name=program.name,
            uw_dept=program.underwriting_department,
            calculation_date=calculation_date,
            source_program=source_program,
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
    else:
        print("6. Skipping detailed run persistence (simplified mode)")
        print()

    print("=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nAll results saved in: {analysis_subdir}")


if __name__ == "__main__":
    main()
