import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
from io import StringIO
import tempfile
from src.managers import ProgramManager
from src.domain.bordereau import Bordereau
from src.engine import apply_program_to_bordereau
from src.domain import PRODUCT
from app.visuals import (
    build_program_graph_figure,
    build_timeline_figure,
    build_sankey_figure,
)


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
    program_files = st.file_uploader(
        "Upload your program folder (CSV format)",
        accept_multiple_files="directory",
        type=["csv"],
        help="Select the folder containing program.csv, structures.csv, and conditions.csv",
    )

with col2:
    st.markdown("### 📊 Bordereau")
    bordereau_file = st.file_uploader(
        "Upload your bordereau CSV",
        type=["csv"],
        help="The CSV file containing the policy data to analyze",
    )

if program_files and bordereau_file:
    try:
        with st.spinner("🔄 Loading files..."):
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = Path(tmp_dir)

                uploaded_filenames = []
                for uploaded_file in program_files:
                    filename = Path(uploaded_file.name).name
                    dest_path = tmp_dir_path / filename
                    dest_path.write_bytes(uploaded_file.getbuffer())
                    uploaded_filenames.append(filename)

                required_files = ["program.csv", "structures.csv", "conditions.csv"]
                missing_files = [
                    f for f in required_files if f not in uploaded_filenames
                ]
                if missing_files:
                    raise ValueError(
                        f"Missing required files: {', '.join(missing_files)}"
                    )

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".csv", mode="w", encoding="utf-8"
                ) as tmp_bordereau:
                    bordereau_file.seek(0)
                    tmp_bordereau.write(bordereau_file.read().decode("utf-8"))
                    tmp_bordereau_path = tmp_bordereau.name

                bordereau_df = Bordereau.from_csv(tmp_bordereau_path)
                manager = ProgramManager(backend="csv_folder")
                program = manager.load(str(tmp_dir_path))

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

        col_cd1, col_cd2 = st.columns([2, 1])
        with col_cd1:
            calc_dt_input = st.date_input(
                "Calculation date",
                value=pd.Timestamp.today().date(),
                help="Date used for Loss Occurring structures; Risk Attaching uses policy inception",
            )
        with col_cd2:
            st.write("")
            st.write("")
            st.info("You can change the calculation date before running the analysis")

        calculation_date = pd.to_datetime(calc_dt_input).date().isoformat()

        with st.spinner("🔄 Calculating..."):
            bordereau_with_net, results = apply_program_to_bordereau(
                bordereau_df, program, calculation_date
            )

        st.success(f"✅ Program successfully applied to {len(results)} policies")

        st.markdown("---")
        st.markdown("## 📊 Results by Policy")

        display_df = results.copy()

        priority_columns = [
            "INSURED_NAME",
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
        if "INSURED_NAME" in formatted_df.columns:
            column_config["INSURED_NAME"] = st.column_config.TextColumn(
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

        if "INSURED_NAME" in results.columns and len(results) > 0:
            selected_insured = st.selectbox(
                "Select an insured to view details",
                options=results["INSURED_NAME"].unique(),
            )

            policy_result = results[results["INSURED_NAME"] == selected_insured].iloc[0]

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
                st.markdown("### 🧭 Visualizations")

                st.subheader("Graph: Program DAG")
                try:
                    dag_fig = build_program_graph_figure(
                        policy_result, calculation_date
                    )
                    st.plotly_chart(dag_fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not build DAG figure: {e}")

                st.subheader("Timeline: RA/LO windows vs calculation date")
                try:
                    tl_fig = build_timeline_figure(program, calculation_date)
                    st.plotly_chart(tl_fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not build timeline: {e}")

                st.subheader("Sankey: Exposure → Cessions → Reinsurer/Retention")
                try:
                    gross = policy_result.get("exposure", 0.0) or 0.0
                    sankey_fig = build_sankey_figure(policy_result, gross)
                    st.plotly_chart(sankey_fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not build sankey: {e}")

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
                                f"**Layer Cession (100%):** {struct.get('ceded_to_layer_100pct', 0.0):,.2f}"
                            )
                            if struct.get("signed_share") is not None:
                                st.write(
                                    f"**Reinsurer Share:** {struct['signed_share']:.4f} ({struct['signed_share']*100:.2f}%)"
                                )
                            st.write(
                                f"**Cession to Reinsurer:** {struct.get('ceded_to_reinsurer', 0.0):,.2f}"
                            )

                            # Display applied terms from flattened typed fields
                            st.markdown("**Applied Terms:**")
                            params_df_data = []
                            if struct["type_of_participation"] == PRODUCT.QUOTA_SHARE:
                                if pd.notna(
                                    pd.Series([struct.get("cession_pct")]).iloc[0]
                                ):
                                    params_df_data.append(
                                        {
                                            "Parameter": "CESSION_PCT",
                                            "Value": f"{struct['cession_pct']}",
                                        }
                                    )
                                if pd.notna(pd.Series([struct.get("limit")]).iloc[0]):
                                    params_df_data.append(
                                        {
                                            "Parameter": "LIMIT",
                                            "Value": f"{struct['limit']:,.0f}",
                                        }
                                    )
                            elif (
                                struct["type_of_participation"]
                                == PRODUCT.EXCESS_OF_LOSS
                            ):
                                if pd.notna(
                                    pd.Series([struct.get("attachment")]).iloc[0]
                                ):
                                    params_df_data.append(
                                        {
                                            "Parameter": "ATTACHMENT",
                                            "Value": f"{struct['attachment']:,.0f}",
                                        }
                                    )
                                if pd.notna(pd.Series([struct.get("limit")]).iloc[0]):
                                    params_df_data.append(
                                        {
                                            "Parameter": "LIMIT",
                                            "Value": f"{struct['limit']:,.0f}",
                                        }
                                    )
                            if pd.notna(
                                pd.Series([struct.get("signed_share")]).iloc[0]
                            ):
                                params_df_data.append(
                                    {
                                        "Parameter": "SIGNED_SHARE",
                                        "Value": f"{struct['signed_share']}",
                                    }
                                )

                            if params_df_data:
                                st.table(pd.DataFrame(params_df_data))

                            # Matching condition summary from matching_details
                            md = struct.get("matching_details") or {}
                            dim_matches = md.get("dimension_matches") or {}
                            conditions = []
                            for dim in program.dimension_columns:
                                d = dim_matches.get(dim) or {}
                                cond_vals = d.get("condition_values")
                                if cond_vals is not None and len(cond_vals) > 0:
                                    conditions.append(
                                        f"{dim}={','.join(map(str, cond_vals))}"
                                    )
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
        "👆 Please upload a program folder (CSV format) and a bordereau (CSV) to start the analysis"
    )
