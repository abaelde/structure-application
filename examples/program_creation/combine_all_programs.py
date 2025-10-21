"""
Combine all individual program files into a single all_programs CSV folder

This script simulates what would happen in a real database with multiple programs:
- Reads all CSV folders from examples/programs/
- Renumbers IDs sequentially (like auto-increment in a database)
- Concatenates all programs, structures, and conditions
- Outputs a single all_programs folder with 3 CSV files
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pandas as pd
import numpy as np
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.managers import ProgramManager


def combine_all_programs(programs_dir: str, output_dir: str):
    """
    Combine all program files into a single CSV folder with renumbered IDs

    Args:
        programs_dir: Directory containing individual program CSV folders
        output_dir: Output path for the combined all_programs folder
    """
    programs_path = Path(programs_dir)

    # Find all CSV folders (excluding all_programs itself if it exists)
    program_folders = sorted(
        [f for f in programs_path.iterdir() if f.is_dir() and f.name != "all_programs"]
    )

    if not program_folders:
        print(f"No program folders found in {programs_dir}")
        return

    print(f"Found {len(program_folders)} program folders:")
    for f in program_folders:
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

    # Process each program folder
    for program_folder in program_folders:
        print(f"Processing {program_folder.name}...")

        try:
            # Read the three CSV files
            program_csv = program_folder / "program.csv"
            structures_csv = program_folder / "structures.csv"
            conditions_csv = program_folder / "conditions.csv"
            
            if not all([program_csv.exists(), structures_csv.exists(), conditions_csv.exists()]):
                print(f"  WARNING: Missing CSV files in {program_folder.name}, skipping")
                continue
                
            program_df = pd.read_csv(program_csv)
            structures_df = pd.read_csv(structures_csv)
            conditions_df = pd.read_csv(conditions_csv)

            # Get original IDs
            old_reprog_id = program_df["REINSURANCE_PROGRAM_ID"].iloc[0]
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
            program_df_new["REINSURANCE_PROGRAM_ID"] = program_df_new["REINSURANCE_PROGRAM_ID"].map(
                reprog_id_map
            )

            # Apply new IDs to structures
            structures_df_new = structures_df.copy()
            structures_df_new["INSPER_ID_PRE"] = structures_df_new["INSPER_ID_PRE"].map(
                insper_id_map
            )
            structures_df_new["REINSURANCE_PROGRAM_ID"] = structures_df_new["REINSURANCE_PROGRAM_ID"].map(
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
            conditions_df_new["REINSURANCE_PROGRAM_ID"] = conditions_df_new["REINSURANCE_PROGRAM_ID"].map(
                reprog_id_map
            )

            # Log the mappings
            print(f"  REINSURANCE_PROGRAM_ID: {old_reprog_id} -> {reprog_id_map[old_reprog_id]}")
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
            print(f"  ERROR processing {program_folder.name}: {e}")
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

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Write to CSV files
    print(f"Writing to {output_dir}...")
    combined_programs.to_csv(output_path / "program.csv", index=False)
    combined_structures.to_csv(output_path / "structures.csv", index=False)
    combined_conditions.to_csv(output_path / "conditions.csv", index=False)
    
    # Check if exclusions exist and combine them too
    all_exclusions = []
    for program_folder in program_folders:
        exclusions_csv = program_folder / "exclusions.csv"
        if exclusions_csv.exists():
            exclusions_df = pd.read_csv(exclusions_csv)
            # Renumber exclusion IDs if they exist
            if "EXCLUSION_ID" in exclusions_df.columns:
                # Map exclusion IDs to new sequential IDs
                old_exclusion_ids = exclusions_df["EXCLUSION_ID"].values
                exclusion_id_map = {}
                for old_id in old_exclusion_ids:
                    if old_id not in exclusion_id_map:
                        exclusion_id_map[old_id] = len(exclusion_id_map) + 1
                exclusions_df["EXCLUSION_ID"] = exclusions_df["EXCLUSION_ID"].map(exclusion_id_map)
            all_exclusions.append(exclusions_df)
    
    if all_exclusions:
        combined_exclusions = pd.concat(all_exclusions, ignore_index=True)
        combined_exclusions.to_csv(output_path / "exclusions.csv", index=False)
        print(f"Total exclusions: {len(combined_exclusions)}")

    print(f"✅ Successfully created {output_dir}")
    print()

    # Display summary
    print("=" * 80)
    print("SUMMARY OF COMBINED PROGRAMS")
    print("=" * 80)
    print("\nPrograms:")
    print(combined_programs[["REINSURANCE_PROGRAM_ID", "TITLE"]].to_string(index=False))
    print("\nStructures by Program:")
    structure_summary = combined_structures.groupby("REINSURANCE_PROGRAM_ID").agg(
        {
            "INSPER_ID_PRE": ["count", "min", "max"],
            "BUSINESS_TITLE": lambda x: ", ".join(x.astype(str)),
        }
    )
    print(structure_summary)
    print("\nconditions by Program:")
    condition_summary = combined_conditions.groupby("REINSURANCE_PROGRAM_ID").agg(
        {"BUSCL_ID_PRE": ["count", "min", "max"]}
    )
    print(condition_summary)


if __name__ == "__main__":
    # Directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    programs_dir = os.path.join(script_dir, "..", "programs")
    output_dir = os.path.join(programs_dir, "all_programs")

    print("=" * 80)
    print("COMBINING ALL PROGRAMS INTO SINGLE CSV FOLDER")
    print("=" * 80)
    print()

    combine_all_programs(programs_dir, output_dir)

    print("\n" + "=" * 80)
    print("DONE")
    print("=" * 80)
