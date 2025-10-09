"""
Program to Bordereau Mapping Configuration

This file defines the mapping between reinsurance programs and their corresponding bordereaux.
Each program can be associated with one or more bordereaux for testing and application.

Usage:
    from examples.program_bordereau_mapping import PROGRAM_BORDEREAU_MAPPING

    # Get bordereau for a specific program
    bordereau_path = PROGRAM_BORDEREAU_MAPPING.get("aviation_axa_xl_2024")

    # Get all mappings
    for program, bordereau in PROGRAM_BORDEREAU_MAPPING.items():
        print(f"{program} -> {bordereau}")
"""

import os
from pathlib import Path

# Base directories
EXAMPLES_DIR = Path(__file__).parent
PROGRAMS_DIR = EXAMPLES_DIR / "programs"
BORDEREAUX_DIR = EXAMPLES_DIR / "bordereaux"


# ============================================================================
# PROGRAM TO BORDEREAU MAPPING
# ============================================================================
# Key: Program filename (without .xlsx extension)
# Value: Bordereau filename (without .csv extension)
#
# Note: Add new mappings as new programs and bordereaux are created
# ============================================================================

PROGRAM_BORDEREAU_MAPPING = {
    # Aviation Programs
    "aviation_axa_xl_2024": "aviation/bordereau_aviation_axa_xl",
    "aviation_old_republic_2024": "aviation/bordereau_aviation_old_republic",
    # Casualty Programs
    # TODO: Create bordereau for casualty_aig_2024
    "casualty_aig_2024": None,
    # Simple Test Programs
    # TODO: Create bordereau for single_excess_of_loss
    "single_excess_of_loss": None,
    # TODO: Create bordereau for single_quota_share
    "single_quota_share": None,
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_program_path(program_name: str) -> Path:
    """
    Get the full path to a program file

    Args:
        program_name: Program name (with or without .xlsx extension)

    Returns:
        Path to the program file
    """
    if not program_name.endswith(".xlsx"):
        program_name = f"{program_name}.xlsx"
    return PROGRAMS_DIR / program_name


def get_bordereau_path(bordereau_name: str) -> Path:
    """
    Get the full path to a bordereau file

    Args:
        bordereau_name: Bordereau name (with or without .csv extension)
                       Can include subdirectory (e.g., "aviation/bordereau_aviation_axa_xl")

    Returns:
        Path to the bordereau file
    """
    if bordereau_name is None:
        return None
    if not bordereau_name.endswith(".csv"):
        bordereau_name = f"{bordereau_name}.csv"
    return BORDEREAUX_DIR / bordereau_name


def get_mapped_bordereau(program_name: str) -> Path:
    """
    Get the bordereau path mapped to a specific program

    Args:
        program_name: Program name (with or without .xlsx extension)

    Returns:
        Path to the bordereau file, or None if no mapping exists
    """
    # Remove extension if present
    program_key = program_name.replace(".xlsx", "")
    bordereau_name = PROGRAM_BORDEREAU_MAPPING.get(program_key)
    return get_bordereau_path(bordereau_name)


def list_all_mappings(include_missing: bool = True) -> dict:
    """
    List all program-bordereau mappings with their file paths

    Args:
        include_missing: If False, exclude programs without bordereaux

    Returns:
        Dictionary with program names as keys and mapping info as values
    """
    mappings = {}
    for program_name, bordereau_name in PROGRAM_BORDEREAU_MAPPING.items():
        if not include_missing and bordereau_name is None:
            continue

        program_path = get_program_path(program_name)
        bordereau_path = get_bordereau_path(bordereau_name)

        mappings[program_name] = {
            "program_path": program_path,
            "program_exists": program_path.exists(),
            "bordereau_name": bordereau_name,
            "bordereau_path": bordereau_path,
            "bordereau_exists": bordereau_path.exists() if bordereau_path else False,
            "ready": (
                program_path.exists()
                and bordereau_path is not None
                and bordereau_path.exists()
            ),
        }

    return mappings


def get_missing_bordereaux() -> list:
    """
    Get list of programs that don't have a bordereau assigned

    Returns:
        List of program names without bordereaux
    """
    return [
        program
        for program, bordereau in PROGRAM_BORDEREAU_MAPPING.items()
        if bordereau is None
    ]


def get_ready_pairs() -> list:
    """
    Get list of (program, bordereau) pairs that are ready to use

    Returns:
        List of tuples (program_path, bordereau_path)
    """
    ready_pairs = []
    for program_name, info in list_all_mappings(include_missing=False).items():
        if info["ready"]:
            ready_pairs.append((info["program_path"], info["bordereau_path"]))
    return ready_pairs


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================


def display_mapping_status():
    """Display a formatted status of all program-bordereau mappings"""
    print("=" * 80)
    print("PROGRAM TO BORDEREAU MAPPING STATUS")
    print("=" * 80)
    print()

    mappings = list_all_mappings()

    for program_name, info in mappings.items():
        status = "✅ READY" if info["ready"] else "⚠️  INCOMPLETE"
        print(f"{status} | {program_name}")
        print(f"  Program:   {info['program_path']}")
        print(f"             {'✓ exists' if info['program_exists'] else '✗ missing'}")

        if info["bordereau_name"]:
            print(f"  Bordereau: {info['bordereau_path']}")
            print(
                f"             {'✓ exists' if info['bordereau_exists'] else '✗ missing'}"
            )
        else:
            print(f"  Bordereau: None (TODO: create bordereau)")
        print()

    # Summary
    ready_count = sum(1 for info in mappings.values() if info["ready"])
    total_count = len(mappings)
    missing = get_missing_bordereaux()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total programs: {total_count}")
    print(f"Ready pairs: {ready_count}")
    print(f"Missing bordereaux: {len(missing)}")
    if missing:
        print(f"  Programs without bordereaux:")
        for prog in missing:
            print(f"    - {prog}")


if __name__ == "__main__":
    # Display mapping status when run directly
    display_mapping_status()
