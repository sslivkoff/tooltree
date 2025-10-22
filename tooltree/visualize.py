from __future__ import annotations

import typing
from . import colors
from . import types

if typing.TYPE_CHECKING:
    import polars as pl
    import plotly.graph_objects as go  # type: ignore
    from typing import Mapping


def create_treemap_figure(
    treemap_data: types.TreemapData,
    *,
    metric: str,
    color_branches: list[str] | dict[str, str | None] | None = None,
    color_nodes: str | Mapping[str | tuple[str, ...], typing.Any] | None = None,
    color_root: str | None = None,
    cmap: str | None = None,
    cmin: int | float | None = None,
    cmid: int | float | None = None,
    cmax: int | float | None = None,
    color_bar: bool = False,
    height: int | None = None,
    width: int | None = None,
    max_depth: int | None = None,
    treemap_object_kwargs: dict[str, typing.Any] | None = None,
    layout_kwargs: dict[str, typing.Any] | None = None,
    trace_kwargs: dict[str, typing.Any] | None = None,
) -> go.Figure:
    import plotly.graph_objects as go

    # get color kwargs
    treemap_color_kwargs, layout_color_kwargs = colors._get_color_kwargs(
        treemap_data=treemap_data,
        color_branches=color_branches,
        color_nodes=color_nodes,
        color_root=color_root,
        cmap=cmap,
        cmin=cmin,
        cmid=cmid,
        cmax=cmax,
        color_bar=color_bar,
        metric=metric,
    )

    # compile general treemap kwargs
    if treemap_object_kwargs is None:
        treemap_object_kwargs = {}
    for key, value in {'maxdepth': max_depth}.items():
        if key in treemap_object_kwargs and value is not None:
            raise ValueError(key + ' in both args and treemap_object_kwargs')
        treemap_object_kwargs[key] = value
    treemap_object_kwargs.setdefault(
        'textfont', dict(family='monospace', size=20)
    )

    # generate figure
    treemap_obj = go.Treemap(
        ids=treemap_data['ids'],
        labels=treemap_data['labels'],
        parents=treemap_data['parents'],
        values=treemap_data['sizes'],
        customdata=treemap_data['tooltips'],
        branchvalues='total',
        **treemap_object_kwargs,
        **treemap_color_kwargs,
    )
    fig = go.Figure(treemap_obj)

    # update layout
    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),
        height=height,
        width=width,
        **layout_color_kwargs,
    )
    if layout_kwargs is not None:
        fig.update_layout(**layout_kwargs)

    # update traces
    fig.update_traces(
        marker_line_width=0.5,
        textposition='middle center',
        hovertemplate='%{customdata}<extra></extra>',
        hoverlabel={'font': {'size': 22, 'family': 'Monospace'}},
        marker_pad={'l': 5, 'b': 5, 't': 30, 'r': 5},
        selector=dict(type='treemap'),
    )
    if trace_kwargs is not None:
        fig.update_traces(**trace_kwargs)

    return fig
