import streamlit as st
import pandas as pd
from pathlib import Path
from io import StringIO
import tempfile
from src.managers import ProgramManager
from src.domain.bordereau import Bordereau
from src.engine import apply_program_to_bordereau
from src.domain import FIELDS, PRODUCT

st.set_page_config(
    page_title="Reinsurance Program Analyzer",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #6c757d;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
    }
    .upload-condition {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-header">🏢 Reinsurance Program Analyzer</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Analyze your reinsurance program application in real-time</div>',
    unsafe_allow_html=True,
)

st.markdown("## 📤 File Upload")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📋 Reinsurance Program")
    program_file = st.file_uploader(
        "Upload your program Excel file",
        type=["xlsx"],
        help="The Excel file containing the reinsurance program configuration",
    )

with col2:
    st.markdown("### 📊 Bordereau")
    bordereau_file = st.file_uploader(
        "Upload your bordereau CSV",
        type=["csv"],
        help="The CSV file containing the policy data to analyze",
    )

if program_file and bordereau_file:
    try:
        with st.spinner("🔄 Loading files..."):
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".xlsx"
            ) as tmp_program:
                tmp_program.write(program_file.read())
                tmp_program_path = tmp_program.name

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".csv", mode="w", encoding="utf-8"
            ) as tmp_bordereau:
                bordereau_file.seek(0)
                tmp_bordereau.write(bordereau_file.read().decode("utf-8"))
                tmp_bordereau_path = tmp_bordereau.name

            bordereau_df = Bordereau.from_csv(tmp_bordereau_path)
            manager = ProgramManager(backend="excel")
            program = manager.load(tmp_program_path)

            Path(tmp_program_path).unlink()
            Path(tmp_bordereau_path).unlink()

        st.success(f"✅ Files loaded successfully!")

        st.markdown("---")
        st.markdown("## 📋 Program Configuration")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Program Name", program.name)
        with col2:
            st.metric("Number of Structures", len(program.structures))
        with col3:
            st.metric("Policies Loaded", len(bordereau_df))

        with st.expander("🔍 Program Details", expanded=False):
            buffer = StringIO()
            program.describe(file=buffer)
            st.text(buffer.getvalue())

        st.markdown("---")
        st.markdown("## ⚙️ Program Application")

        with st.spinner("🔄 Calculating..."):
            calculation_date = "2024-06-01"  # Date de calcul par défaut
            bordereau_with_net, results = apply_program_to_bordereau(
                bordereau_df, program, calculation_date
            )

        st.success(f"✅ Program successfully applied to {len(results)} policies")

        st.markdown("---")
        st.markdown("## 📊 Results by Policy")

        display_df = results.copy()

        priority_columns = [
            FIELDS["INSURED_NAME"],
            "exposure",
            "cession_to_layer_100pct",
            "cession_to_reinsurer",
            "retained_by_cedant",
        ]

        available_priority_columns = [
            col for col in priority_columns if col in display_df.columns
        ]

        columns_to_exclude = ["structures_detail"]
        other_columns = [
            col
            for col in display_df.columns
            if col not in available_priority_columns and col not in columns_to_exclude
        ]

        display_columns = available_priority_columns + other_columns

        formatted_df = display_df[display_columns].copy()

        numeric_columns = [
            "exposure",
            "cession_to_layer_100pct",
            "cession_to_reinsurer",
            "retained_by_cedant",
        ]
        for col in numeric_columns:
            if col in formatted_df.columns:
                formatted_df[col] = formatted_df[col].apply(
                    lambda x: f"{x:,.2f}" if pd.notna(x) else ""
                )

        column_config = {}
        if FIELDS["INSURED_NAME"] in formatted_df.columns:
            column_config[FIELDS["INSURED_NAME"]] = st.column_config.TextColumn(
                "Insured", width="medium"
            )
        if "exposure" in formatted_df.columns:
            column_config["exposure"] = st.column_config.TextColumn("Gross Exposure")
        if "cession_to_layer_100pct" in formatted_df.columns:
            column_config["cession_to_layer_100pct"] = st.column_config.TextColumn(
                "Layer Cession (100%)"
            )
        if "cession_to_reinsurer" in formatted_df.columns:
            column_config["cession_to_reinsurer"] = st.column_config.TextColumn(
                "Reinsurer Cession"
            )
        if "retained_by_cedant" in formatted_df.columns:
            column_config["retained_by_cedant"] = st.column_config.TextColumn(
                "Cedant Retention"
            )

        st.dataframe(
            formatted_df,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### 🔍 Policy Details")

        if FIELDS["INSURED_NAME"] in results.columns and len(results) > 0:
            selected_insured = st.selectbox(
                "Select an insured to view details",
                options=results[FIELDS["INSURED_NAME"]].unique(),
            )

            policy_result = results[
                results[FIELDS["INSURED_NAME"]] == selected_insured
            ].iloc[0]

            st.markdown(f"#### 📋 {selected_insured}")

            col1, col2 = st.columns(2)
            with col1:
                if "exposure" in policy_result:
                    st.metric(
                        "Cedant Gross Exposure", f"{policy_result['exposure']:,.2f}"
                    )
                if "cession_to_layer_100pct" in policy_result:
                    st.metric(
                        "Layer Cession (100%)",
                        f"{policy_result['cession_to_layer_100pct']:,.2f}",
                    )

            with col2:
                if "cession_to_reinsurer" in policy_result:
                    st.metric(
                        "Reinsurer Cession",
                        f"{policy_result['cession_to_reinsurer']:,.2f}",
                    )
                if "retained_by_cedant" in policy_result:
                    st.metric(
                        "Cedant Retention",
                        f"{policy_result['retained_by_cedant']:,.2f}",
                    )

            if (
                "structures_detail" in policy_result
                and policy_result["structures_detail"]
            ):
                st.markdown("##### Applied Structures:")

                for i, struct in enumerate(policy_result["structures_detail"], 1):
                    status = (
                        "✅ APPLIED"
                        if struct.get("applied", False)
                        else "❌ NOT APPLIED"
                    )

                    with st.expander(
                        f"{i}. {struct['structure_name']} ({struct['type_of_participation']}) - {status}",
                        expanded=struct.get("applied", False),
                    ):
                        if struct.get("predecessor_title"):
                            st.info(
                                f"**Predecessor:** {struct['predecessor_title']} (Inuring)"
                            )
                        else:
                            st.info("**Predecessor:** None (Entry point)")

                        st.write(f"**Input Exposure:** {struct['input_exposure']:,.2f}")

                        if struct.get("applied", False):
                            st.write(
                                f"**Layer Cession (100%):** {struct['cession_to_layer_100pct']:,.2f}"
                            )
                            st.write(
                                f"**Reinsurer Share:** {struct['reinsurer_share']:.4f} ({struct['reinsurer_share']*100:.2f}%)"
                            )
                            st.write(
                                f"**Cession to Reinsurer:** {struct['cession_to_reinsurer']:,.2f}"
                            )

                            if struct.get("condition"):
                                condition = struct["condition"]
                                st.markdown("**Applied condition Parameters:**")

                                params_df_data = []
                                if (
                                    struct["type_of_participation"]
                                    == PRODUCT.QUOTA_SHARE
                                ):
                                    if pd.notna(condition.get("CESSION_PCT")):
                                        params_df_data.append(
                                            {
                                                "Parameter": "CESSION_PCT",
                                                "Value": f"{condition['CESSION_PCT']}",
                                            }
                                        )
                                    if pd.notna(condition.get("LIMIT")):
                                        params_df_data.append(
                                            {
                                                "Parameter": "LIMIT_100",
                                                "Value": f"{condition['LIMIT']:,.0f}",
                                            }
                                        )

                                elif (
                                    struct["type_of_participation"]
                                    == PRODUCT.EXCESS_OF_LOSS
                                ):
                                    rescaling_info = struct.get("rescaling_info")
                                    if rescaling_info:
                                        st.warning(
                                            f"⚠️ RESCALED (Retention factor: {rescaling_info['retention_factor']:.2%})"
                                        )
                                        if (
                                            rescaling_info["original_attachment"]
                                            is not None
                                        ):
                                            params_df_data.append(
                                                {
                                                    "Parameter": "ATTACHMENT_POINT_100",
                                                    "Value": f"{rescaling_info['original_attachment']:,.0f} → {rescaling_info['rescaled_attachment']:,.0f}",
                                                }
                                            )
                                        if rescaling_info["original_limit"] is not None:
                                            params_df_data.append(
                                                {
                                                    "Parameter": "LIMIT_100",
                                                    "Value": f"{rescaling_info['original_limit']:,.0f} → {rescaling_info['rescaled_limit']:,.0f}",
                                                }
                                            )
                                    else:
                                        if pd.notna(
                                            condition.get("ATTACHMENT_POINT_100")
                                        ):
                                            params_df_data.append(
                                                {
                                                    "Parameter": "ATTACHMENT_POINT_100",
                                                    "Value": f"{condition['ATTACHMENT_POINT_100']:,.0f}",
                                                }
                                            )
                                        if pd.notna(condition.get("LIMIT")):
                                            params_df_data.append(
                                                {
                                                    "Parameter": "LIMIT_100",
                                                    "Value": f"{condition['LIMIT']:,.0f}",
                                                }
                                            )

                                if pd.notna(condition.get("SIGNED_SHARE_PCT")):
                                    params_df_data.append(
                                        {
                                            "Parameter": "SIGNED_SHARE_PCT",
                                            "Value": f"{condition['SIGNED_SHARE_PCT']}",
                                        }
                                    )

                                if params_df_data:
                                    st.table(pd.DataFrame(params_df_data))

                                conditions = []
                                for dim in program.dimension_columns:
                                    value = condition.get(dim)
                                    if pd.notna(value):
                                        conditions.append(f"{dim}={value}")
                                conditions_str = (
                                    ", ".join(conditions)
                                    if conditions
                                    else "All (no conditions)"
                                )
                                st.write(f"**Matching Conditions:** {conditions_str}")
                        else:
                            st.warning("**Reason:** No matching condition found")

        st.markdown("---")
        st.markdown("## 💾 Export Results")

        col1, col2 = st.columns(2)

        with col1:
            csv_bordereau = bordereau_with_net.to_csv(index=False)
            st.download_button(
                label="📥 Download Bordereau with Cessions",
                data=csv_bordereau,
                file_name="bordereau_with_cession.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col2:
            results_for_export = results.drop(
                columns=["structures_detail"], errors="ignore"
            )
            csv_results = results_for_export.to_csv(index=False)
            st.download_button(
                label="📥 Download Detailed Results",
                data=csv_results,
                file_name="detailed_results.csv",
                mime="text/csv",
                use_container_width=True,
            )

    except Exception as e:
        st.error(f"❌ Processing error: {e}")
        st.exception(e)

else:
    st.info(
        "👆 Please upload a program file (Excel) and a bordereau (CSV) to start the analysis"
    )
