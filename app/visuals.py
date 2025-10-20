import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx


def _fmt_pct(x):
    try:
        return f"{float(x)*100:.2f}%"
    except Exception:
        return str(x)


def _scope_str(scope_set):
    if not scope_set:
        return "total"
    return " + ".join(sorted(scope_set))


def _cond_param_lines(struct, cond, rescaling_info=None):
    if not cond:
        return []
    lines = []
    typ = struct.get("type_of_participation")
    if typ == "quota_share":
        if cond.get("CESSION_PCT") is not None:
            lines.append(f"CESSION_PCT: {_fmt_pct(cond.get('CESSION_PCT'))}")
        if cond.get("LIMIT_100") is not None:
            lines.append(f"LIMIT_100: {cond.get('LIMIT_100'):,.0f}")
    elif typ == "excess_of_loss":
        if rescaling_info:
            oa, ra = rescaling_info.get("original_attachment"), rescaling_info.get(
                "rescaled_attachment"
            )
            ol, rl = rescaling_info.get("original_limit"), rescaling_info.get(
                "rescaled_limit"
            )
            if oa is not None:
                lines.append(f"ATTACHMENT: {oa:,.0f} → {ra:,.0f}")
            if ol is not None:
                lines.append(f"LIMIT: {ol:,.0f} → {rl:,.0f}")
        else:
            if cond.get("ATTACHMENT_POINT_100") is not None:
                lines.append(f"ATTACHMENT: {cond.get('ATTACHMENT_POINT_100'):,.0f}")
            if cond.get("LIMIT_100") is not None:
                lines.append(f"LIMIT: {cond.get('LIMIT_100'):,.0f}")
    if cond.get("SIGNED_SHARE_PCT") is not None:
        lines.append(f"SIGNED_SHARE: {_fmt_pct(cond.get('SIGNED_SHARE_PCT'))}")
    return lines


def _color_for_status(applied: bool, reason: str | None):
    if applied:
        return "#2ECC71"
    if reason == "out_of_period":
        return "#95A5A6"
    if reason == "no_matching_condition":
        return "#E67E22"
    return "#BDC3C7"


def build_program_graph_figure(policy_result_row, calculation_date):
    details = policy_result_row.get("structures_detail", [])
    G = nx.DiGraph()
    G.add_node("START", label="Start", color="#3498DB")

    by_name = {s["structure_name"]: s for s in details}

    for s in details:
        name = s["structure_name"]
        applied = s.get("applied", False)
        reason = s.get("reason")
        color = _color_for_status(applied, reason)
        cbasis = (s.get("matching_details") or {}).get("claim_basis") or (
            s.get("condition") or {}
        ).get("INSPER_CLAIM_BASIS_CD")
        cbasis = cbasis or "—"

        input_exp = s.get("input_exposure", 0.0)
        c_layer = s.get("cession_to_layer_100pct", 0.0)
        c_reins = s.get("cession_to_reinsurer", 0.0)
        reins_share = s.get("reinsurer_share", 0.0)
        scope = _scope_str(
            set(s.get("scope", "").split(";"))
            if isinstance(s.get("scope"), str)
            else s.get("scope", set())
        )

        cond = s.get("condition") or {}
        params = _cond_param_lines(s, cond, s.get("rescaling_info"))

        status_text = "APPLIED ✅" if applied else f"NOT APPLIED ❌ ({reason or 'n/a'})"
        tooltip_lines = [
            f"<b>{name}</b>",
            f"Status: {status_text}",
            f"Claim basis: {cbasis}",
            f"Scope: {scope}",
            f"Input: {input_exp:,.2f}",
        ]
        if applied:
            tooltip_lines += [
                f"Cession (layer 100%): {c_layer:,.2f}",
                f"Cession to reinsurer: {c_reins:,.2f}",
                f"Reinsurer share: {_fmt_pct(reins_share)}",
            ]
        if params:
            tooltip_lines.append("<br/>".join(params))
        tooltip = "<br/>".join(tooltip_lines)

        G.add_node(name, label=name, color=color, title=tooltip)

    for s in details:
        name = s["structure_name"]
        pred = s.get("predecessor_title")
        if pred and pred in by_name:
            G.add_edge(pred, name)
        else:
            G.add_edge("START", name)

    pos = nx.spring_layout(G, k=1.2, seed=42)

    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    edge_trace = go.Scatter(
        x=list(edge_x), y=list(edge_y), mode="lines", hoverinfo="none"
    )

    node_x, node_y, texts, colors, hover = [], [], [], [], []
    for n, data in G.nodes(data=True):
        x, y = pos[n]
        node_x.append(x)
        node_y.append(y)
        texts.append(data.get("label", n))
        colors.append(data.get("color", "#7F8C8D"))
        hover.append(data.get("title", data.get("label", n)))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=texts,
        textposition="bottom center",
        hovertext=hover,
        hoverinfo="text",
        marker=dict(size=24, line=dict(width=1, color="#2C3E50"), color=colors),
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="Program DAG (applied / skipped)",
        showlegend=False,
        hovermode="closest",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    fig.update_layout(title=f"Program DAG — calculation_date={calculation_date}")
    return fig


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
    calc_dt = pd.to_datetime(calculation_date, errors="coerce")
    if pd.notna(calc_dt):
        fig.add_vline(
            x=calc_dt.to_pydatetime(),
            line_width=2,
            line_dash="dash",
            annotation_text="calculation_date",
            annotation_position="top",
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

        c_layer = s.get("cession_to_layer_100pct", 0.0) or 0.0
        c_reins = s.get("cession_to_reinsurer", 0.0) or 0.0
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
