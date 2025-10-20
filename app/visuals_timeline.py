import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


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
    df = df.dropna(subset=["Start", "Finish"]).copy()
    if df.empty:
        return go.Figure()
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


