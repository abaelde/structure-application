"""
Example script showing how to use program-bordereau mapping

This script demonstrates how to:
1. Load the program-bordereau mapping
2. Apply a program to its corresponding bordereau
3. Generate results
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

import pandas as pd
from structures.structure_loader import ProgramLoader
from structures.structure_engine import apply_program_to_bordereau
from structures.program_display import display_program
from examples.program_bordereau_mapping import (
    get_ready_pairs,
    get_mapped_bordereau,
    get_program_path,
    display_mapping_status,
)


def apply_program_to_mapped_bordereau(program_name: str):
    """
    Apply a program to its mapped bordereau

    Args:
        program_name: Name of the program (without .xlsx extension)
    """
    print("=" * 80)
    print(f"APPLYING PROGRAM: {program_name}")
    print("=" * 80)
    print()

    # Get paths from mapping
    program_path = get_program_path(program_name)
    bordereau_path = get_mapped_bordereau(program_name)

    if not program_path.exists():
        print(f"❌ Error: Program file not found: {program_path}")
        return

    if bordereau_path is None:
        print(f"⚠️  Warning: No bordereau mapped for program '{program_name}'")
        print("   Please update examples/program_bordereau_mapping.py")
        return

    if not bordereau_path.exists():
        print(f"❌ Error: Bordereau file not found: {bordereau_path}")
        return

    print(f"📊 Program:   {program_path.name}")
    print(f"📋 Bordereau: {bordereau_path.name}")
    print()

    # Load program
    print("Loading program...")
    loader = ProgramLoader(str(program_path))
    program = loader.get_program()

    # Display program structure
    display_program(program)

    # Load bordereau
    print("\nLoading bordereau...")
    bordereau_df = pd.read_csv(bordereau_path)
    print(f"Loaded {len(bordereau_df)} policies")
    print()

    # Apply program to bordereau
    print("Applying program to bordereau...")
    bordereau_with_net, results = apply_program_to_bordereau(bordereau_df, program)

    # Display results summary
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(
        results[["policy_number", "exposure", "cession_to_layer_100pct", "cession_to_reinsurer", "retained"]]
    )
    print()

    # Statistics
    total_exposure = results["exposure"].sum()
    total_cession_to_layer_100pct = results["cession_to_layer_100pct"].sum()
    total_cession_to_reinsurer = results["cession_to_reinsurer"].sum()
    total_retained = results["retained"].sum()

    print("=" * 80)
    print("STATISTICS")
    print("=" * 80)
    print(f"Total exposure:              {total_exposure:,.2f}")
    print(f"Total cession at layer (100%): {total_cession_to_layer_100pct:,.2f}")
    print(f"Total cession to reinsurer:  {total_cession_to_reinsurer:,.2f}")
    print(f"Total retained:              {total_retained:,.2f}")
    print(
        f"Cession rate:                {(total_cession_to_reinsurer / total_exposure * 100) if total_exposure > 0 else 0:.2f}%"
    )
    print()


def apply_all_ready_programs():
    """Apply all programs that have a ready bordereau mapping"""
    print("=" * 80)
    print("APPLYING ALL READY PROGRAM-BORDEREAU PAIRS")
    print("=" * 80)
    print()

    ready_pairs = get_ready_pairs()

    if not ready_pairs:
        print("⚠️  No ready program-bordereau pairs found")
        print("   Please create bordereaux or update the mapping")
        return

    print(f"Found {len(ready_pairs)} ready pair(s)")
    print()

    for program_path, bordereau_path in ready_pairs:
        program_name = program_path.stem  # filename without extension
        apply_program_to_mapped_bordereau(program_name)
        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Apply programs to their mapped bordereaux"
    )
    parser.add_argument(
        "program",
        nargs="?",
        help="Specific program name to apply (without .xlsx). If not provided, shows mapping status.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Apply all ready program-bordereau pairs",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show mapping status",
    )

    args = parser.parse_args()

    if args.status or (not args.program and not args.all):
        # Show mapping status by default
        display_mapping_status()
    elif args.all:
        # Apply all ready pairs
        apply_all_ready_programs()
    elif args.program:
        # Apply specific program
        apply_program_to_mapped_bordereau(args.program)
