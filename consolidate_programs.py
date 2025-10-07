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
from structures.structure_loader import ProgramLoader
from structures.structure_engine import apply_program_to_bordereau
from structures.program_display import display_program
from examples.program_bordereau_mapping import (
    get_ready_pairs,
    get_mapped_bordereau,
    get_program_path,
    PROGRAM_BORDEREAU_MAPPING,
)


def apply_single_program_to_bordereau(program_path: Path, bordereau_path: Path):
    """
    Apply a single program to its bordereau

    Args:
        program_path: Path to the program Excel file
        bordereau_path: Path to the bordereau CSV file

    Returns:
        Tuple of (program_name, bordereau_df, results_df)
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

    return program_name, bordereau_with_net, results


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

    for program_path, bordereau_path in ready_pairs:
        try:
            program_name, bordereau_with_net, results = (
                apply_single_program_to_bordereau(program_path, bordereau_path)
            )
            all_results.append(results)
            all_bordereaux.append(bordereau_with_net)
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

    # Aggregate by underlying policy
    print("Aggregating by policy number...")

    # Group by policy to get consolidated view
    policy_aggregation = (
        consolidated_results.groupby("policy_number")
        .agg(
            {
                "exposure": "first",  # Same exposure per policy
                "cession_to_layer_100pct": "sum",  # Sum across all cedants
                "cession_to_reinsurer": "sum",  # Sum across all cedants (= OUR NET EXPOSURE)
                "retained_by_cedant": "first",  # Take the final retained (from last application)
                "cedant_program": lambda x: ", ".join(
                    sorted(set(x))
                ),  # List all cedants
            }
        )
        .reset_index()
    )


    # Display consolidated results - ONLY BY POLICY (meaningful aggregation)
    print("\n" + "=" * 80)
    print("CONSOLIDATED RESULTS BY POLICY (Reinsurer View)")
    print("=" * 80)
    print(
        f"\nNote: Aggregation by policy number across {len(ready_pairs)} cedant(s)."
    )
    print("Each policy may appear in multiple bordereaux (different cedants).\n")
    print(
        policy_aggregation[
            [
                "policy_number",
                "exposure",
                "cession_to_reinsurer",
                "retained_by_cedant",
                "cedant_program",
            ]
        ].to_string(index=False)
    )
    
    print(f"\n  Total policies consolidated: {len(policy_aggregation)}")

    # Save consolidated results
    output_dir = Path("consolidated_results")
    output_dir.mkdir(exist_ok=True)

    # Save policy-level aggregation (the only meaningful aggregation)
    policy_aggregation_file = output_dir / "consolidated_results_by_policy.csv"
    policy_aggregation.to_csv(policy_aggregation_file, index=False)
    print(f"\n✅ Policy aggregation saved to: {policy_aggregation_file}")

    # Save detailed results for reference
    consolidated_results_file = output_dir / "consolidated_results_detailed.csv"
    consolidated_results.to_csv(consolidated_results_file, index=False)
    print(f"✅ Detailed results saved to: {consolidated_results_file}")

    print("\n" + "=" * 80)
    print("CONSOLIDATION COMPLETE")
    print("=" * 80)

    return consolidated_results, policy_aggregation


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
