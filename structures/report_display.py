import pandas as pd
import sys
from typing import Dict, Any
from .constants import PRODUCT, SECTION_COLS as SC


def write_detailed_results(
    results_df: pd.DataFrame, dimension_columns: list, file=None
):
    if file is None:
        file = sys.stdout

    file.write("=" * 80 + "\n")
    file.write("DETAILED BREAKDOWN BY POLICY\n")
    file.write("=" * 80 + "\n")

    for _, policy_result in results_df.iterrows():
        file.write(f"\n{'─' * 80}\n")
        file.write(f"INSURED: {policy_result['insured_name']}\n")
        file.write(f"Cedant gross exposure: {policy_result['exposure']:,.2f}\n")
        file.write(f"Cession at layer (100%): {policy_result['cession_to_layer_100pct']:,.2f}\n")
        file.write(f"Reinsurer net exposure: {policy_result['cession_to_reinsurer']:,.2f}\n")
        file.write(f"Retained by cedant: {policy_result['retained_by_cedant']:,.2f}\n")
        file.write(f"\nStructures applied:\n")

        for i, struct in enumerate(policy_result["structures_detail"], 1):
            status = "✓ APPLIED" if struct.get("applied", False) else "✗ NOT APPLIED"
            file.write(
                f"\n{i}. {struct['structure_name']} ({struct['type_of_participation']}) - {status}\n"
            )
            file.write(f"   Input exposure: {struct['input_exposure']:,.2f}\n")

            if struct.get("applied", False):
                file.write(f"   Cession at layer (100%): {struct['cession_to_layer_100pct']:,.2f}\n")
                file.write(
                    f"   Reinsurer Share: {struct['reinsurer_share']:.4f} ({struct['reinsurer_share']*100:.2f}%)\n"
                )
                file.write(f"   Cession to reinsurer: {struct['cession_to_reinsurer']:,.2f}\n")
                
                if struct.get("section"):
                    section = struct["section"]
                    file.write(f"   Applied section parameters:\n")

                    if struct["type_of_participation"] == PRODUCT.QUOTA_SHARE:
                        if pd.notna(section.get(SC.CESSION_PCT)):
                            file.write(f"      CESSION_PCT: {section[SC.CESSION_PCT]}\n")
                        if pd.notna(section.get(SC.LIMIT)):
                            file.write(f"      LIMIT_100: {section[SC.LIMIT]}\n")
                    elif struct["type_of_participation"] == PRODUCT.EXCESS_OF_LOSS:
                        if pd.notna(section.get(SC.ATTACHMENT)):
                            file.write(
                                f"      ATTACHMENT_POINT_100: {section[SC.ATTACHMENT]}\n"
                            )
                        if pd.notna(section.get(SC.LIMIT)):
                            file.write(f"      LIMIT_100: {section[SC.LIMIT]}\n")

                    if pd.notna(section.get(SC.SIGNED_SHARE)):
                        file.write(
                            f"      SIGNED_SHARE_PCT: {section[SC.SIGNED_SHARE]}\n"
                        )

                    conditions = []
                    for dim in dimension_columns:
                        value = section.get(dim)
                        if pd.notna(value):
                            conditions.append(f"{dim}={value}")
                    conditions_str = (
                        ", ".join(conditions) if conditions else "All (no conditions)"
                    )
                    file.write(f"   Matching conditions: {conditions_str}\n")
            else:
                file.write(f"   Reason: No matching section found\n")


def generate_detailed_report(
    results_df: pd.DataFrame,
    program: Dict[str, Any],
    output_file: str = "detailed_report.txt",
):
    from .program_display import write_program_config

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("DETAILED STRUCTURES APPLICATION REPORT\n")
        f.write("=" * 80 + "\n\n")

        write_program_config(program, file=f)
        f.write("\n\n")

        write_detailed_results(results_df, program["dimension_columns"], file=f)

    print(f"✓ Detailed report generated: {output_file}")

