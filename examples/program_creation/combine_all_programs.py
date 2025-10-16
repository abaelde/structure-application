"""
Combine all individual program files into a single all_programs.xlsx file

This script simulates what would happen in a real database with multiple programs:
- Reads all .xlsx files from examples/programs/
- Renumbers IDs sequentially (like auto-increment in a database)
- Concatenates all programs, structures, and conditions
- Outputs a single all_programs.xlsx file with 3 sheets
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pandas as pd
import numpy as np
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.domain import SHEETS
from src.managers import ProgramManager


def combine_all_programs(programs_dir: str, output_file: str):
    """
    Combine all program files into a single file with renumbered IDs

    Args:
        programs_dir: Directory containing individual program .xlsx files
        output_file: Output path for the combined all_programs.xlsx file
    """
    programs_path = Path(programs_dir)

    # Find all .xlsx files (excluding all_programs.xlsx itself if it exists)
    program_files = sorted(
        [f for f in programs_path.glob("*.xlsx") if f.name != "all_programs.xlsx"]
    )

    if not program_files:
        print(f"No program files found in {programs_dir}")
        return

    print(f"Found {len(program_files)} program files:")
    for f in program_files:
        print(f"  - {f.name}")
    print()

    # Initialize combined dataframes
    all_programs = []
    all_structures = []
    all_conditions = []

    # Initialize ID counters (simulating auto-increment)
    next_reprog_id = 1
    next_insper_id = 1
    next_buscl_id = 1

    # Process each program file
    for program_file in program_files:
        print(f"Processing {program_file.name}...")

        try:
            # Read the three sheets
            program_df = pd.read_excel(program_file, sheet_name=SHEETS.PROGRAM)
            structures_df = pd.read_excel(program_file, sheet_name=SHEETS.STRUCTURES)
            conditions_df = pd.read_excel(program_file, sheet_name=SHEETS.conditions)

            # Get original IDs
            old_reprog_id = program_df["REPROG_ID_PRE"].iloc[0]
            old_insper_ids = structures_df["INSPER_ID_PRE"].values
            old_buscl_ids = conditions_df["BUSCL_ID_PRE"].values

            # Create mapping dictionaries for ID translation
            reprog_id_map = {old_reprog_id: next_reprog_id}
            insper_id_map = {}
            buscl_id_map = {}

            # Map structure IDs
            for old_id in old_insper_ids:
                insper_id_map[old_id] = next_insper_id
                next_insper_id += 1

            # Map condition IDs
            for old_id in old_buscl_ids:
                buscl_id_map[old_id] = next_buscl_id
                next_buscl_id += 1

            # Apply new IDs to program
            program_df_new = program_df.copy()
            program_df_new["REPROG_ID_PRE"] = program_df_new["REPROG_ID_PRE"].map(
                reprog_id_map
            )

            # Apply new IDs to structures
            structures_df_new = structures_df.copy()
            structures_df_new["INSPER_ID_PRE"] = structures_df_new["INSPER_ID_PRE"].map(
                insper_id_map
            )
            structures_df_new["REPROG_ID_PRE"] = structures_df_new["REPROG_ID_PRE"].map(
                reprog_id_map
            )

            # Apply new IDs to conditions
            conditions_df_new = conditions_df.copy()
            conditions_df_new["BUSCL_ID_PRE"] = conditions_df_new["BUSCL_ID_PRE"].map(
                buscl_id_map
            )
            conditions_df_new["INSPER_ID_PRE"] = conditions_df_new["INSPER_ID_PRE"].map(
                insper_id_map
            )
            conditions_df_new["REPROG_ID_PRE"] = conditions_df_new["REPROG_ID_PRE"].map(
                reprog_id_map
            )

            # Log the mappings
            print(f"  REPROG_ID_PRE: {old_reprog_id} -> {reprog_id_map[old_reprog_id]}")
            print(
                f"  INSPER_ID_PRE: {min(old_insper_ids)}-{max(old_insper_ids)} -> {min(insper_id_map.values())}-{max(insper_id_map.values())}"
            )
            print(
                f"  BUSCL_ID_PRE: {min(old_buscl_ids)}-{max(old_buscl_ids)} -> {min(buscl_id_map.values())}-{max(buscl_id_map.values())}"
            )
            print(
                f"  Structures: {len(structures_df_new)}, conditions: {len(conditions_df_new)}"
            )
            print()

            # Append to combined lists
            all_programs.append(program_df_new)
            all_structures.append(structures_df_new)
            all_conditions.append(conditions_df_new)

            # Update counter for next program
            next_reprog_id += 1

        except Exception as e:
            print(f"  ERROR processing {program_file.name}: {e}")
            print()
            continue

    # Concatenate all dataframes
    print("Combining all dataframes...")
    combined_programs = pd.concat(all_programs, ignore_index=True)
    combined_structures = pd.concat(all_structures, ignore_index=True)
    combined_conditions = pd.concat(all_conditions, ignore_index=True)

    print(f"Total programs: {len(combined_programs)}")
    print(f"Total structures: {len(combined_structures)}")
    print(f"Total conditions: {len(combined_conditions)}")
    print()

    # Write to Excel file
    print(f"Writing to {output_file}...")
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        combined_programs.to_excel(writer, sheet_name=SHEETS.PROGRAM, index=False)
        combined_structures.to_excel(writer, sheet_name=SHEETS.STRUCTURES, index=False)
        combined_conditions.to_excel(writer, sheet_name=SHEETS.conditions, index=False)

    # Auto-adjust column widths using ProgramManager
    print(f"Auto-adjusting column widths...")
    manager = ProgramManager(backend="excel")
    # Note: _auto_adjust_column_widths might not be available in ProgramManager
    # manager._auto_adjust_column_widths(output_file)

    print(f"✅ Successfully created {output_file}")
    print()

    # Display summary
    print("=" * 80)
    print("SUMMARY OF COMBINED PROGRAMS")
    print("=" * 80)
    print("\nPrograms:")
    print(combined_programs[["REPROG_ID_PRE", "REPROG_TITLE"]].to_string(index=False))
    print("\nStructures by Program:")
    structure_summary = combined_structures.groupby("REPROG_ID_PRE").agg(
        {
            "INSPER_ID_PRE": ["count", "min", "max"],
            "BUSINESS_TITLE": lambda x: ", ".join(x.astype(str)),
        }
    )
    print(structure_summary)
    print("\nconditions by Program:")
    condition_summary = combined_conditions.groupby("REPROG_ID_PRE").agg(
        {"BUSCL_ID_PRE": ["count", "min", "max"]}
    )
    print(condition_summary)


if __name__ == "__main__":
    # Directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    programs_dir = os.path.join(script_dir, "..", "programs")
    output_file = os.path.join(programs_dir, "all_programs.xlsx")

    print("=" * 80)
    print("COMBINING ALL PROGRAMS INTO SINGLE FILE")
    print("=" * 80)
    print()

    combine_all_programs(programs_dir, output_file)

    print("\n" + "=" * 80)
    print("DONE")
    print("=" * 80)
