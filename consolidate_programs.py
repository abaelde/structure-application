"""
Consolidation Script - Apply Multiple Programs and Aggregate Results

This script represents the real-world use case:
1. Each program corresponds to a cedant (cédante)
2. Each program has its own bordereau
3. Apply each program to its corresponding bordereau
4. Aggregate results by underlying policy across all cedants

This provides a consolidated view of reinsurance cessions across multiple cedants.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))

import pandas as pd
from pathlib import Path
from datetime import datetime
from structures.structure_loader import ProgramLoader
from structures.structure_engine import apply_program_to_bordereau
from structures.program_display import display_program
from examples.program_bordereau_mapping import (
    get_ready_pairs,
    get_mapped_bordereau,
    get_program_path,
    PROGRAM_BORDEREAU_MAPPING,
)


def generate_consolidated_report(
    report_path: Path,
    all_program_info: list,
    ready_pairs: list,
    consolidated_results: pd.DataFrame,
    insured_aggregation: pd.DataFrame,
):
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("CONSOLIDATED REPORT - MULTI-CEDANT REINSURANCE ANALYSIS\n")
        f.write("=" * 80 + "\n")
        f.write(f"\nReport generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Number of cedants processed: {len(ready_pairs)}\n")
        f.write("\n")

        # Section 1: Program Processing Details
        f.write("=" * 80 + "\n")
        f.write("SECTION 1: PROGRAM PROCESSING DETAILS\n")
        f.write("=" * 80 + "\n\n")

        for i, prog_info in enumerate(all_program_info, 1):
            f.write(f"Cedant #{i}: {prog_info['program_name']}\n")
            f.write("-" * 80 + "\n")
            f.write(f"  Program Display Name: {prog_info['program_display_name']}\n")
            f.write(f"  Program File:         {prog_info['program_file']}\n")
            f.write(f"  Bordereau File:       {prog_info['bordereau_file']}\n")
            f.write(f"  Number of Structures: {prog_info['num_structures']}\n")
            f.write(f"  Policies in Bordereau: {prog_info['num_policies']}\n")
            f.write(f"  Processed Policies:   {prog_info['num_results']}\n")
            f.write("\n")

        # Section 2: Consolidated Results by Insured
        f.write("\n" + "=" * 80 + "\n")
        f.write("SECTION 2: CONSOLIDATED RESULTS BY INSURED (REINSURER VIEW)\n")
        f.write("=" * 80 + "\n\n")
        f.write(
            f"Note: Aggregation by insured name (nom_assure) across {len(ready_pairs)} cedant(s).\n"
        )
        f.write(
            "Same insured may appear in multiple bordereaux with different policy numbers.\n\n"
        )

        # Write insured aggregation table
        f.write(
            insured_aggregation[
                [
                    "nom_assure",
                    "exposure",
                    "cession_to_reinsurer",
                    "retained_by_cedant",
                    "cedant_program",
                    "policy_number",
                ]
            ].to_string(index=False)
        )
        f.write(f"\n\nTotal insureds consolidated: {len(insured_aggregation)}\n")

        # Section 3: Files Generated
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("SECTION 3: OUTPUT FILES GENERATED\n")
        f.write("=" * 80 + "\n\n")
        f.write("The following files have been generated:\n\n")
        f.write(
            "  1. consolidated_results_by_insured.csv  - Aggregated results by insured name\n"
        )
        f.write(
            "  2. consolidated_results_detailed.csv    - Detailed results (one line per policy per program)\n"
        )
        f.write(
            "  3. consolidated_report.txt              - This consolidated report\n"
        )

        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")


def apply_single_program_to_bordereau(program_path: Path, bordereau_path: Path):
    """
    Apply a single program to its bordereau

    Args:
        program_path: Path to the program Excel file
        bordereau_path: Path to the bordereau CSV file

    Returns:
        Tuple of (program_name, program_info, bordereau_df, results_df)
    """
    program_name = program_path.stem

    print(f"\n{'=' * 80}")
    print(f"Processing: {program_name}")
    print(f"{'=' * 80}")
    print(f"📊 Program:   {program_path.name}")
    print(f"📋 Bordereau: {bordereau_path.name}")

    # Load program
    loader = ProgramLoader(str(program_path))
    program = loader.get_program()
    print(
        f"   Loaded program '{program['name']}' with {len(program['structures'])} structures"
    )

    # Load bordereau
    bordereau_df = pd.read_csv(bordereau_path)
    print(f"   Loaded {len(bordereau_df)} policies from bordereau")

    # Apply program to bordereau
    bordereau_with_net, results = apply_program_to_bordereau(bordereau_df, program)

    # Add cedant identifier to results
    results["cedant_program"] = program_name
    results["program_name"] = program["name"]

    print(f"   ✓ Processed {len(results)} policies")

    # Store program info for reporting
    program_info = {
        "program_name": program_name,
        "program_display_name": program["name"],
        "program_file": program_path.name,
        "bordereau_file": bordereau_path.name,
        "num_structures": len(program["structures"]),
        "num_policies": len(bordereau_df),
        "num_results": len(results),
    }

    return program_name, program_info, bordereau_with_net, results


def consolidate_all_programs():
    """
    Main consolidation function:
    1. Apply each program to its mapped bordereau
    2. Aggregate results by underlying policy
    3. Generate consolidated reports
    """
    print("=" * 80)
    print("MULTI-CEDANT CONSOLIDATION")
    print("=" * 80)
    print("\nApplying all ready program-bordereau pairs...")

    # Get all ready pairs
    ready_pairs = get_ready_pairs()

    if not ready_pairs:
        print("\n⚠️  No ready program-bordereau pairs found")
        print("   Please create bordereaux or update the mapping in:")
        print("   examples/program_bordereau_mapping.py")
        return

    print(f"\nFound {len(ready_pairs)} ready pair(s)")

    # Apply each program to its bordereau
    all_results = []
    all_bordereaux = []
    all_program_info = []

    for program_path, bordereau_path in ready_pairs:
        try:
            program_name, program_info, bordereau_with_net, results = (
                apply_single_program_to_bordereau(program_path, bordereau_path)
            )
            all_results.append(results)
            all_bordereaux.append(bordereau_with_net)
            all_program_info.append(program_info)
        except Exception as e:
            print(f"\n❌ Error processing {program_path.name}: {e}")
            import traceback

            traceback.print_exc()
            continue

    if not all_results:
        print("\n❌ No programs were successfully processed")
        return

    # Consolidate all results
    print(f"\n\n{'=' * 80}")
    print("CONSOLIDATING RESULTS ACROSS ALL CEDANTS")
    print(f"{'=' * 80}\n")

    consolidated_results = pd.concat(all_results, ignore_index=True)

    # Aggregate by insured name (underlying insured entity)
    print("Aggregating by insured name (nom_assure)...")
    
    # Add nom_assure from bordereau to results
    # We need to merge with the original bordereaux to get nom_assure
    for bordereau_df in all_bordereaux:
        # Merge nom_assure into consolidated_results based on matching policy_number
        if 'nom_assure' in bordereau_df.columns:
            consolidated_results = consolidated_results.merge(
                bordereau_df[['numero_police', 'nom_assure']],
                left_on='policy_number',
                right_on='numero_police',
                how='left',
                suffixes=('', '_from_bordereau')
            )
            # Keep only nom_assure if we don't have it yet
            if 'nom_assure' not in consolidated_results.columns or consolidated_results['nom_assure'].isna().all():
                if 'nom_assure_from_bordereau' in consolidated_results.columns:
                    consolidated_results['nom_assure'] = consolidated_results['nom_assure'].fillna(consolidated_results['nom_assure_from_bordereau'])
            # Clean up temporary columns
            consolidated_results = consolidated_results.drop(columns=[c for c in consolidated_results.columns if '_from_bordereau' in c or c == 'numero_police'], errors='ignore')

    # Group by insured name to get consolidated view
    insured_aggregation = (
        consolidated_results.groupby("nom_assure")
        .agg(
            {
                "exposure": "sum",  # Sum exposure across all cedants for same insured
                "cession_to_layer_100pct": "sum",  # Sum across all cedants
                "cession_to_reinsurer": "sum",  # Sum across all cedants (= OUR NET EXPOSURE)
                "retained_by_cedant": "sum",  # Sum retained across all cedants
                "cedant_program": lambda x: ", ".join(
                    sorted(set(x))
                ),  # List all cedants
                "policy_number": lambda x: ", ".join(
                    sorted(set(x))
                ),  # List all policy numbers
            }
        )
        .reset_index()
    )


    # Display consolidated results - BY INSURED (meaningful aggregation)
    print("\n" + "=" * 80)
    print("CONSOLIDATED RESULTS BY INSURED (Reinsurer View)")
    print("=" * 80)
    print(
        f"\nNote: Aggregation by insured name (nom_assure) across {len(ready_pairs)} cedant(s)."
    )
    print("Same insured may appear in multiple bordereaux with different policy numbers.\n")
    print(
        insured_aggregation[
            [
                "nom_assure",
                "exposure",
                "cession_to_reinsurer",
                "retained_by_cedant",
                "cedant_program",
                "policy_number",
            ]
        ].to_string(index=False)
    )
    
    print(f"\n  Total insureds consolidated: {len(insured_aggregation)}")

    # Save consolidated results
    output_dir = Path("consolidated_results")
    output_dir.mkdir(exist_ok=True)

    # Save insured-level aggregation (the only meaningful aggregation)
    insured_aggregation_file = output_dir / "consolidated_results_by_insured.csv"
    insured_aggregation.to_csv(insured_aggregation_file, index=False)
    print(f"\n✅ Insured aggregation saved to: {insured_aggregation_file}")

    # Save detailed results for reference (one line per policy per program)
    consolidated_results_file = output_dir / "consolidated_results_detailed.csv"
    consolidated_results.to_csv(consolidated_results_file, index=False)
    print(f"✅ Detailed results saved to: {consolidated_results_file}")

    # Generate consolidated report
    report_file = output_dir / "consolidated_report.txt"
    generate_consolidated_report(
        report_file,
        all_program_info,
        ready_pairs,
        consolidated_results,
        insured_aggregation,
    )
    print(f"✅ Consolidated report saved to: {report_file}")

    print("\n" + "=" * 80)
    print("CONSOLIDATION COMPLETE")
    print("=" * 80)

    return consolidated_results, insured_aggregation


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Consolidate multiple cedant programs and aggregate by policy"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Display detailed program structures",
    )

    args = parser.parse_args()

    # Run consolidation
    consolidate_all_programs()
