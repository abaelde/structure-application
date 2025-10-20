from .visuals_graph import build_program_graph_figure
from .visuals_timeline import build_timeline_figure
from .visuals_sankey import build_sankey_figure

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

__all__ = [
    "build_program_graph_figure",
    "build_timeline_figure",
    "build_sankey_figure",
]


def build_timeline_figure(program, calculation_date):
    rows = []
    for st_struct in program.structures:
        rows.append(
            {
                "Structure": st_struct.structure_name,
                "Claim Basis": st_struct.claim_basis,
                "Start": pd.to_datetime(st_struct.inception_date, errors="coerce"),
                "Finish": pd.to_datetime(st_struct.expiry_date, errors="coerce"),
            }
        )
    if not rows:
        return go.Figure()
    df = pd.DataFrame(rows)
    # Nettoyage et conversions robustes
    df = df.dropna(subset=["Start", "Finish"]).copy()
    if df.empty:
        return go.Figure()
    # Convertir vers datetime Python pour éviter les opérations Timestamp ± int
    df["Start"] = pd.to_datetime(df["Start"]).dt.to_pydatetime()
    df["Finish"] = pd.to_datetime(df["Finish"]).dt.to_pydatetime()

    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish",
        y="Structure",
        color="Claim Basis",
        hover_data=["Claim Basis"],
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(type="date")
    calc_dt = pd.to_datetime(calculation_date, errors="coerce")
    if pd.notna(calc_dt):
        xdt = calc_dt.to_pydatetime()
        # Use a shape to avoid Plotly's internal mean over mixed types
        fig.add_shape(
            type="line",
            x0=xdt,
            x1=xdt,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line=dict(width=2, dash="dash", color="#444"),
        )
        fig.add_annotation(
            x=xdt,
            y=1,
            xref="x",
            yref="paper",
            text="calculation_date",
            showarrow=False,
            yshift=10,
        )
    fig.update_layout(
        title="Structures timeline (RA uses policy inception, LO uses calculation date)",
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def build_sankey_figure(policy_result_row, gross_exposure: float):
    details = [
        d for d in policy_result_row.get("structures_detail", []) if d.get("applied")
    ]
    if not details:
        return go.Figure(layout_title_text="No cessions for this policy")

    labels = ["Gross Exposure"]
    node_index = {"Gross Exposure": 0}

    def add_node(name):
        if name not in node_index:
            node_index[name] = len(labels)
            labels.append(name)

    add_node("Reinsurer")
    add_node("Cedant Retention")

    sources, targets, values, hover = [], [], [], []

    retained_prev = gross_exposure

    for s in details:
        name = s["structure_name"]
        add_node(name)
        idx_struct = node_index[name]

        c_layer = s.get("ceded_to_layer_100pct", 0.0) or 0.0
        c_reins = s.get("ceded_to_reinsurer", 0.0) or 0.0
        retained_after = s.get("retained_after", None)
        if retained_after is None:
            retained_after = max(retained_prev - c_layer, 0.0)

        sources.append(node_index["Gross Exposure"])
        targets.append(idx_struct)
        values.append(c_layer)
        hover.append(f"{name}: cession to layer (100%) = {c_layer:,.2f}")

        sources.append(idx_struct)
        targets.append(node_index["Reinsurer"])
        values.append(c_reins)
        hover.append(f"{name}: cession to reinsurer = {c_reins:,.2f}")

        retained_delta = max(retained_prev - retained_after, 0.0)
        if retained_delta > 0:
            sources.append(idx_struct)
            targets.append(node_index["Cedant Retention"])
            values.append(retained_delta)
            hover.append(f"{name}: additional retention = {retained_delta:,.2f}")

        retained_prev = retained_after

    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(label=labels, pad=20, thickness=18),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    hovertemplate=[h + "<extra></extra>" for h in hover],
                ),
            )
        ]
    )
    fig.update_layout(
        title_text="Exposure flow: Gross → Structures → Reinsurer / Retention",
        font_size=12,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig
