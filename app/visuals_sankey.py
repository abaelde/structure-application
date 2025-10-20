import plotly.graph_objects as go


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

