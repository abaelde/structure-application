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

    # Display summary statistics for this program
    total_exposure = results["exposure"].sum()
    total_gross_ceded = results["gross_ceded"].sum()
    total_net_ceded = results["net_ceded"].sum()
    total_retained = results["retained"].sum()

    print(f"\n   Summary for {program_name}:")
    print(f"   - Total exposure:    {total_exposure:,.2f}")
    print(f"   - Total gross ceded: {total_gross_ceded:,.2f}")
    print(f"   - Total net ceded:   {total_net_ceded:,.2f}")
    print(f"   - Total retained:    {total_retained:,.2f}")
    print(
        f"   - Cession rate:      {(total_net_ceded / total_exposure * 100) if total_exposure > 0 else 0:.2f}%"
    )

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
                "gross_ceded": "sum",  # Sum across all cedants
                "net_ceded": "sum",  # Sum across all cedants
                "retained": "first",  # Take the final retained (from last application)
                "cedant_program": lambda x: ", ".join(
                    sorted(set(x))
                ),  # List all cedants
            }
        )
        .reset_index()
    )

    # Add computed fields
    policy_aggregation["total_ceded_pct"] = (
        policy_aggregation["net_ceded"] / policy_aggregation["exposure"] * 100
    )
    policy_aggregation["retained_pct"] = (
        policy_aggregation["retained"] / policy_aggregation["exposure"] * 100
    )

    # Display consolidated results
    print("\n" + "=" * 80)
    print("CONSOLIDATED RESULTS BY POLICY")
    print("=" * 80)
    print(
        policy_aggregation[
            [
                "policy_number",
                "exposure",
                "gross_ceded",
                "net_ceded",
                "retained",
                "total_ceded_pct",
                "cedant_program",
            ]
        ].to_string(index=False)
    )

    # Overall statistics
    print("\n\n" + "=" * 80)
    print("OVERALL CONSOLIDATED STATISTICS")
    print("=" * 80)

    total_exposure = policy_aggregation["exposure"].sum()
    total_gross_ceded = policy_aggregation["gross_ceded"].sum()
    total_net_ceded = policy_aggregation["net_ceded"].sum()
    total_retained = policy_aggregation["retained"].sum()

    print(f"\nTotal across all cedants:")
    print(f"  Policies:         {len(policy_aggregation)}")
    print(f"  Cedants:          {len(ready_pairs)}")
    print(f"  Total exposure:   {total_exposure:,.2f}")
    print(f"  Total gross ceded: {total_gross_ceded:,.2f}")
    print(f"  Total net ceded:   {total_net_ceded:,.2f}")
    print(f"  Total retained:    {total_retained:,.2f}")
    print(
        f"  Overall cession rate: {(total_net_ceded / total_exposure * 100) if total_exposure > 0 else 0:.2f}%"
    )

    # Statistics by cedant
    print("\n" + "=" * 80)
    print("STATISTICS BY CEDANT")
    print("=" * 80)

    cedant_stats = (
        consolidated_results.groupby(["cedant_program", "program_name"])
        .agg(
            {
                "policy_number": "count",
                "exposure": "sum",
                "gross_ceded": "sum",
                "net_ceded": "sum",
                "retained": "sum",
            }
        )
        .reset_index()
    )

    cedant_stats["cession_rate_pct"] = (
        cedant_stats["net_ceded"] / cedant_stats["exposure"] * 100
    )
    cedant_stats.columns = [
        "Cedant",
        "Program Name",
        "Policies",
        "Exposure",
        "Gross Ceded",
        "Net Ceded",
        "Retained",
        "Cession %",
    ]

    print("\n" + cedant_stats.to_string(index=False))

    # Save consolidated results
    output_dir = Path("consolidated_results")
    output_dir.mkdir(exist_ok=True)

    # Save detailed results
    consolidated_results_file = output_dir / "consolidated_results_detailed.csv"
    consolidated_results.to_csv(consolidated_results_file, index=False)
    print(f"\n✅ Detailed results saved to: {consolidated_results_file}")

    # Save policy-level aggregation
    policy_aggregation_file = output_dir / "consolidated_results_by_policy.csv"
    policy_aggregation.to_csv(policy_aggregation_file, index=False)
    print(f"✅ Policy aggregation saved to: {policy_aggregation_file}")

    # Save cedant statistics
    cedant_stats_file = output_dir / "statistics_by_cedant.csv"
    cedant_stats.to_csv(cedant_stats_file, index=False)
    print(f"✅ Cedant statistics saved to: {cedant_stats_file}")

    print("\n" + "=" * 80)
    print("CONSOLIDATION COMPLETE")
    print("=" * 80)

    return consolidated_results, policy_aggregation, cedant_stats


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
