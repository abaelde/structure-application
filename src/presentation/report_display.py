import pandas as pd
import sys
from typing import Dict, Any
from src.domain import PRODUCT, condition_COLS as SC, Program


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
        file.write(f"INSURED: {policy_result['INSURED_NAME']}\n")
        file.write(f"Cedant gross exposure: {policy_result['exposure']:,.2f}\n")
        file.write(
            f"Cession at layer (100%): {policy_result['cession_to_layer_100pct']:,.2f}\n"
        )
        file.write(
            f"Reinsurer net exposure: {policy_result['cession_to_reinsurer']:,.2f}\n"
        )
        file.write(f"Retained by cedant: {policy_result['retained_by_cedant']:,.2f}\n")
        file.write(f"\nStructures applied:\n")

        for i, struct in enumerate(policy_result["structures_detail"], 1):
            status = "✓ APPLIED" if struct.get("applied", False) else "✗ NOT APPLIED"
            file.write(
                f"\n{i}. {struct['structure_name']} ({struct['type_of_participation']}) - {status}\n"
            )

            # Afficher le prédécesseur s'il existe
            if struct.get("predecessor_title"):
                file.write(f"   Predecessor: {struct['predecessor_title']} (Inuring)\n")
            else:
                file.write(f"   Predecessor: None (Entry point)\n")

            file.write(f"   Input exposure: {struct['input_exposure']:,.2f}\n")

            if struct.get("applied", False):
                file.write(
                    f"   Cession at layer (100%): {struct['ceded_to_layer_100pct']:,.2f}\n"
                )
                file.write(
                    f"   Reinsurer Share: {struct['signed_share']:.4f} ({struct['signed_share']*100:.2f}%)\n"
                )
                file.write(
                    f"   Cession to reinsurer: {struct['ceded_to_reinsurer']:,.2f}\n"
                )

                if struct.get("condition"):
                    condition = struct["condition"]
                    rescaling_info = struct.get("rescaling_info")

                    file.write(f"   Applied condition parameters:\n")

                    if struct["type_of_participation"] == PRODUCT.QUOTA_SHARE:
                        if pd.notna(condition.get(SC.CESSION_PCT)):
                            file.write(
                                f"      CESSION_PCT: {condition[SC.CESSION_PCT]}\n"
                            )
                        if pd.notna(condition.get(SC.LIMIT)):
                            file.write(f"      LIMIT_100: {condition[SC.LIMIT]}\n")
                    elif struct["type_of_participation"] == PRODUCT.EXCESS_OF_LOSS:
                        # Afficher les limites rescalées si applicable
                        if rescaling_info:
                            file.write(
                                f"      ⚠️ RESCALED (Retention factor: {rescaling_info['retention_factor']:.2%})\n"
                            )
                            if rescaling_info["original_attachment"] is not None:
                                file.write(
                                    f"      ATTACHMENT_POINT_100: {rescaling_info['original_attachment']:,.0f} → {rescaling_info['rescaled_attachment']:,.0f}\n"
                                )
                            if rescaling_info["original_limit"] is not None:
                                file.write(
                                    f"      LIMIT_100: {rescaling_info['original_limit']:,.0f} → {rescaling_info['rescaled_limit']:,.0f}\n"
                                )
                        else:
                            if pd.notna(condition.get(SC.ATTACHMENT)):
                                file.write(
                                    f"      ATTACHMENT_POINT_100: {condition[SC.ATTACHMENT]:,.0f}\n"
                                )
                            if pd.notna(condition.get(SC.LIMIT)):
                                file.write(
                                    f"      LIMIT_100: {condition[SC.LIMIT]:,.0f}\n"
                                )

                    if pd.notna(condition.get(SC.SIGNED_SHARE)):
                        file.write(
                            f"      SIGNED_SHARE_PCT: {condition[SC.SIGNED_SHARE]}\n"
                        )

                    conditions = []
                    for dim in dimension_columns:
                        value = condition.get(dim)
                        if pd.notna(value):
                            conditions.append(f"{dim}={value}")
                    conditions_str = (
                        ", ".join(conditions) if conditions else "All (no conditions)"
                    )
                    file.write(f"   Matching conditions: {conditions_str}\n")

                    # Afficher les détails de matching si disponibles
                    matching_details = struct.get("matching_details")
                    if matching_details:
                        file.write(f"   Matching details:\n")

                        # Afficher les valeurs de la police
                        policy_values = matching_details.get("policy_values", {})
                        if policy_values:
                            file.write(f"      Policy values: ")
                            policy_parts = []
                            for dim, value in policy_values.items():
                                if value is not None:
                                    policy_parts.append(f"{dim}={value}")
                            file.write(f"{', '.join(policy_parts)}\n")

                        # Afficher les détails de matching par dimension
                        dimension_matches = matching_details.get(
                            "dimension_matches", {}
                        )
                        if dimension_matches:
                            file.write(f"      Dimension matching:\n")
                            for dim, match_info in dimension_matches.items():
                                if match_info.get("condition_values") is not None:
                                    cond_vals = match_info["condition_values"]
                                    policy_val = match_info["policy_value"]
                                    matches = match_info["matches"]
                                    status = "✓" if matches else "✗"
                                    file.write(
                                        f"         {status} {dim}: policy='{policy_val}' vs condition={cond_vals}\n"
                                    )
                                else:
                                    file.write(
                                        f"         - {dim}: no constraint (applies to all)\n"
                                    )

                        # Afficher le score de matching
                        matching_score = matching_details.get("matching_score", 0.0)
                        if matching_score > 0:
                            file.write(f"      Matching score: {matching_score:.3f}\n")

                        # Afficher les conditions qui ont échoué
                        failed_conditions = matching_details.get(
                            "failed_conditions", []
                        )
                        if failed_conditions:
                            file.write(
                                f"      Failed conditions: {len(failed_conditions)} other conditions did not match\n"
                            )
                            for i, failed in enumerate(
                                failed_conditions[:3]
                            ):  # Limiter à 3 pour éviter le spam
                                failed_dims = failed.get("failed_dimensions", [])
                                if failed_dims:
                                    file.write(
                                        f"         - Failed on: {', '.join(failed_dims)}\n"
                                    )
            else:
                file.write(f"   Reason: No matching condition found\n")

                # Afficher les détails de pourquoi aucune condition n'a matché
                matching_details = struct.get("matching_details")
                if matching_details:
                    file.write(f"   Why no condition matched:\n")

                    # Afficher les valeurs de la police
                    policy_values = matching_details.get("policy_values", {})
                    if policy_values:
                        file.write(f"      Policy values: ")
                        policy_parts = []
                        for dim, value in policy_values.items():
                            if value is not None:
                                policy_parts.append(f"{dim}={value}")
                        file.write(f"{', '.join(policy_parts)}\n")

                    # Afficher les conditions qui ont échoué
                    failed_conditions = matching_details.get("failed_conditions", [])
                    if failed_conditions:
                        file.write(
                            f"      All {len(failed_conditions)} conditions failed to match:\n"
                        )
                        for i, failed in enumerate(
                            failed_conditions[:5]
                        ):  # Limiter à 5
                            failed_dims = failed.get("failed_dimensions", [])
                            if failed_dims:
                                file.write(
                                    f"         - Condition {i+1}: failed on {', '.join(failed_dims)}\n"
                                )
                    else:
                        file.write(
                            f"      No conditions were defined for this structure\n"
                        )


def generate_detailed_report(
    results_df: pd.DataFrame,
    program: Program,
    output_file: str = "detailed_report.txt",
):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("DETAILED STRUCTURES APPLICATION REPORT\n")
        f.write("=" * 80 + "\n\n")

        program.describe(file=f)
        f.write("\n\n")

        write_detailed_results(results_df, program.dimension_columns, file=f)

    print(f"✓ Detailed report generated: {output_file}")
