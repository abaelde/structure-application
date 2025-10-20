import pandas as pd
import plotly.graph_objects as go
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


def _cond_param_lines(struct):
    """Build parameter lines from flattened typed terms in struct rows.

    Uses keys produced by src/engine/results_terms.terms_as_dict:
    - QS: cession_pct, limit, signed_share
    - XOL: attachment, limit, signed_share
    """
    lines = []
    typ = struct.get("type_of_participation")
    if typ == "quota_share":
        if struct.get("cession_pct") is not None:
            lines.append(f"CESSION_PCT: {_fmt_pct(struct.get('cession_pct'))}")
        if struct.get("limit") is not None:
            lines.append(f"LIMIT: {struct.get('limit'):,.0f}")
    elif typ == "excess_of_loss":
        if struct.get("attachment") is not None:
            lines.append(f"ATTACHMENT: {struct.get('attachment'):,.0f}")
        if struct.get("limit") is not None:
            lines.append(f"LIMIT: {struct.get('limit'):,.0f}")
    if struct.get("signed_share") is not None:
        lines.append(f"SIGNED_SHARE: {_fmt_pct(struct.get('signed_share'))}")
    return lines


def _color_for_status(applied: bool, reason: str | None):
    if applied:
        return "#2ECC71"
    if reason == "out_of_period":
        return "#95A5A6"
    if reason == "no_matching_condition":
        return "#E67E22"
    return "#BDC3C7"


def _linear_positions_from_predecessors(details):
    """
    Compute a left-to-right hierarchical layout based on inuring depth.
    START = level 0, roots = level 1, etc.
    """
    names = [s["structure_name"] for s in details]
    name_set = set(names)
    predecessor = {}
    for s in details:
        pred = s.get("predecessor_title")
        predecessor[s["structure_name"]] = pred if pred in name_set else None

    depth_cache = {}

    def depth(n, seen=None):
        if n in depth_cache:
            return depth_cache[n]
        if seen is None:
            seen = set()
        if n in seen:
            depth_cache[n] = 1
            return 1
        seen.add(n)
        pred = predecessor.get(n)
        if pred is None:
            d = 1
        else:
            d = 1 + depth(pred, seen)
        depth_cache[n] = d
        return d

    levels = {}
    for n in names:
        d = depth(n)
        levels.setdefault(d, []).append(n)

    pos = {"START": (0.0, 0.0)}
    x_gap = 1.6
    y_gap = 1.0

    for lvl in sorted(levels.keys()):
        nodes = levels[lvl]
        mid = (len(nodes) - 1) / 2.0
        for i, n in enumerate(nodes):
            x = x_gap * lvl
            y = y_gap * (i - mid)
            pos[n] = (x, y)

    return pos


def build_program_graph_figure(policy_result_row, calculation_date):
    details = policy_result_row.get("structures_detail", [])
    G = nx.DiGraph()
    G.add_node("START", label="Gross Loss", color="#3498DB")

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

        input_exp = s.get("input_exposure", 0.0) or 0.0
        c_layer = s.get("ceded_to_layer_100pct", 0.0) or 0.0
        c_reins = s.get("ceded_to_reinsurer", 0.0) or 0.0
        reins_share = s.get("signed_share", 0.0) or 0.0
        scope = _scope_str(
            set(s.get("scope", "").split(";"))
            if isinstance(s.get("scope"), str)
            else s.get("scope", set())
        )

        params = _cond_param_lines(s)

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

    pos = _linear_positions_from_predecessors(details)

    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", hoverinfo="none")

    node_x, node_y, texts, colors, hover = [], [], [], [], []
    for n, data in G.nodes(data=True):
        x, y = pos.get(n, (0, 0))
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
        textposition="middle right",
        hovertext=hover,
        hoverinfo="text",
        marker=dict(size=26, line=dict(width=1, color="#2C3E50"), color=colors),
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title=f"Program DAG — linear (left→right) — calculation_date={calculation_date}",
        showlegend=False,
        hovermode="closest",
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig

