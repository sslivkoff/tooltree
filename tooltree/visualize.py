from __future__ import annotations

import typing
from . import build
from . import defaults
from . import types

if typing.TYPE_CHECKING:
    import polars as pl
    import plotly.graph_objects as go  # type: ignore


def create_treemap_figure(
    treemap_data: types.TreemapData,
    *,
    color_branches: list[str] | dict[str, str] | None = None,
    color_nodes: str
    | typing.Mapping[str | tuple[str, ...], typing.Any]
    | None = None,
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
    treemap_color_kwargs, layout_color_kwargs = _get_color_kwargs(
        treemap_data=treemap_data,
        color_branches=color_branches,
        color_nodes=color_nodes,
        color_root=color_root,
        cmap=cmap,
        cmin=cmin,
        cmid=cmid,
        cmax=cmax,
        color_bar=color_bar,
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
        customdata=treemap_data['customdata'],
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


def _get_color_kwargs(
    treemap_data: types.TreemapData,
    color_branches: list[str] | dict[str, str] | None = None,
    color_nodes: str
    | typing.Mapping[str | tuple[str, ...], typing.Any]
    | None = None,
    color_root: str | None = None,
    cmap: str | None = None,
    cmin: int | float | None = None,
    cmid: int | float | None = None,
    cmax: int | float | None = None,
    color_bar: bool = False,
) -> tuple[dict[str, typing.Any], dict[str, typing.Any]]:
    """
    Specifying color:
    1. color_branches=list[str] | list[int]
        - list of colors for main branches, sorted by decreasing size
        - if String type, use as is
        - if Numerical type, use continuous color scale
    2. color_branches=dist[str, str]
        - map from branch name to color, root branches only
    3. color_nodes=list[str] | list[int] | list[float] | pl.Series
        - list of colors for each node, same length as number of nodes
        - if String type, use as is
        - if Numerical type, use continuous color scale
    4. color_nodes=dict[str, str] | dict[str, int] | dict[str, float]
        - map from node name to color
        - if values are String type, use as is
        - if values are Numerical type, use continuous color scale
    5. color_nodes=str
        - column name of node color values
        - if column has String dtype, use as is
        - if column has Numerical dtype, use continuous color scale
    """
    import polars as pl

    treemap_color_kwargs: dict[str, typing.Any] = {'root_color': color_root}
    layout_color_kwargs: dict[str, typing.Any] = {}
    use_color_scale = False

    # set defaults
    if color_branches is None and color_nodes is None:
        color_branches = defaults.default_branch_colors

    # determine color mode
    ids = treemap_data['ids']
    parents = treemap_data['parents']
    root = treemap_data['root']
    if color_branches is not None:
        if isinstance(color_branches, (list, pl.Series)):
            layout_color_kwargs['treemapcolorway'] = color_branches
        elif isinstance(color_branches, dict):
            layout_color_kwargs['treemapcolorway'] = [
                color_branches.get(node_id, 'lightgrey')
                for node_id, parent in zip(ids, parents)
                if parent == root
            ]
        else:
            raise Exception('color_branches must be list or dict or None')
        if len(layout_color_kwargs['treemapcolorway']) > 0:
            use_color_scale = isinstance(
                layout_color_kwargs['treemapcolorway'][0], (int, float)
            )
    elif color_nodes is not None:
        treemap_color_kwargs['marker_colors'] = treemap_data['node_colors']
        if treemap_color_kwargs['marker_colors'] is None:
            raise ValueError('color_nodes column not found in treemap_data')
        if len(treemap_color_kwargs['marker_colors']) > 0:
            use_color_scale = isinstance(
                treemap_color_kwargs['marker_colors'][0], (int, float)
            )
    else:
        raise Exception()

    if use_color_scale:
        treemap_color_kwargs['marker_colorscale'] = cmap
        treemap_color_kwargs['marker_cmin'] = cmin
        treemap_color_kwargs['marker_cmid'] = cmid
        treemap_color_kwargs['marker_cmax'] = cmax
        treemap_color_kwargs['marker_colorbar'] = color_bar

    return treemap_color_kwargs, layout_color_kwargs
