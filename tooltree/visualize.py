from __future__ import annotations

import typing
from . import defaults
from . import types

if typing.TYPE_CHECKING:
    import plotly.graph_objects as go  # type: ignore


def create_figure(
    treemap_data: types.TreemapData,
    *,
    colors: list[str] | None = None,
    height: int | None = None,
) -> go.Figure:
    import plotly.graph_objects as go

    fig = go.Figure(
        go.Treemap(
            labels=treemap_data['names'],
            parents=treemap_data['parents'],
            values=treemap_data['sizes'],
            customdata=treemap_data['customdata'],
            textfont=dict(family='monospace', size=20),
            branchvalues='total',
        )
    )

    if colors is not None:
        colors = defaults.default_colors
    if height is None:
        height = defaults.default_height

    fig.update_layout(
        treemapcolorway=colors,
        margin=dict(l=0, r=0, b=0, t=0),
        height=height,
    )

    fig.update_traces(marker_line_width=0.5)
    fig.update_traces(
        textposition='middle center',
        hovertemplate='<b>%{label}</b><br>%{customdata}<extra></extra>',
        hoverlabel={'font': {'size': 22, 'family': 'Monospace'}},
    )
    fig.update_traces(
        marker_pad={'l': 5, 'b': 5, 't': 30, 'r': 5},
        selector=dict(type='treemap'),
    )


def show_figure(fig: go.Figure) -> None:
    fig.show(config={'displayModeBar': False})


def export_figure_to_html(fig: go.Figure, path: str) -> None:
    fig.write_html(path, config={'displayModeBar': False})
    # fig.write_html(output_path, include_plotlyjs='cdn', full_html=True)
