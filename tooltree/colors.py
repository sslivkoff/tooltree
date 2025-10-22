from __future__ import annotations

import typing
from . import colors
from . import build
from . import defaults
from . import types

if typing.TYPE_CHECKING:
    import polars as pl
    import plotly.graph_objects as go  # type: ignore
    from typing import Mapping


def _get_node_color(
    ancestors: tuple[str, ...] | None,
    level: str | None,
    entry: dict[str, typing.Any] | None,
    color_nodes: str | Mapping[str | tuple[str, ...], typing.Any] | None,
    color_root: str | None,
) -> str | int | float | None:
    """get the color of an individual node for when color_nodes is specificed"""
    if entry is not None and level is not None and ancestors is not None:
        if isinstance(color_nodes, str):
            return entry.get(color_nodes)
        elif isinstance(color_nodes, dict):
            if entry[level] in color_nodes:
                return color_nodes[entry[level]]  # type: ignore
            elif ancestors + (entry[level],) in color_nodes:
                return color_nodes[ancestors + (entry[level],)]  # type: ignore
            else:
                return None
        elif color_nodes is None:
            return None
        else:
            raise Exception('invalid color_nodes: ' + str(color_nodes))
    elif ancestors is None:
        if color_root is not None:
            return color_root
        else:
            return 'white'
    else:
        return None


def _get_color_kwargs(
    treemap_data: types.TreemapData,
    metric: str,
    color_branches: list[str] | dict[str, str | None] | None = None,
    color_nodes: str | Mapping[str | tuple[str, ...], typing.Any] | None = None,
    color_root: str | None = None,
    color_default: str | int | float | None = None,
    cmap: str | None = None,
    cmin: int | float | None = None,
    cmid: int | float | None = None,
    cmax: int | float | None = None,
    color_bar: bool = False,
) -> tuple[dict[str, typing.Any], dict[str, typing.Any]]:
    """return kwargs for go.Treemap() and for fig.update_layout()"""
    import polars as pl

    # return values
    treemap_color_kwargs: dict[str, typing.Any] = {'root_color': color_root}
    layout_color_kwargs: dict[str, typing.Any] = {}

    # set defaults
    if color_branches is None and color_nodes is None:
        color_branches = defaults.default_branch_colors

    # determine color mode
    use_color_scale = False
    ids = treemap_data['ids']
    parents = treemap_data['parents']
    root = treemap_data['root']
    if color_branches is not None:
        if isinstance(color_branches, (list, pl.Series)):
            layout_color_kwargs['treemapcolorway'] = color_branches
        elif isinstance(color_branches, dict):
            if all(isinstance(v, str) for v in color_branches.values()):
                # label colors
                if color_default is None:
                    color_default = defaults.default_branch_color
                layout_color_kwargs['treemapcolorway'] = [
                    color_branches.get(node_id, color_default)
                    for node_id, parent in zip(ids, parents)
                    if parent == root
                ]
            else:
                raise Exception('invalid types in color_branches')
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
            use_color_scale = any(
                isinstance(item, (int, float))
                for item in treemap_color_kwargs['marker_colors']
            )
    else:
        raise Exception()

    if use_color_scale:
        treemap_color_kwargs['marker_colorscale'] = cmap
        treemap_color_kwargs['marker_cmin'] = cmin
        treemap_color_kwargs['marker_cmid'] = cmid
        treemap_color_kwargs['marker_cmax'] = cmax

        if color_bar:
            if isinstance(color_bar, dict):
                cbar: dict[str, typing.Any] = color_bar
            else:
                cbar = {}
            if isinstance(color_nodes, str) and color_nodes != metric:
                cbar.setdefault('title', color_nodes)
            cbar.setdefault(
                'title.font', dict(family='monospace', size=20, color='black')
            )
            cbar.setdefault(
                'tickfont', dict(family='monospace', size=16, color='black')
            )
            treemap_color_kwargs['marker_showscale'] = True
            treemap_color_kwargs['marker_colorbar'] = cbar

    return treemap_color_kwargs, layout_color_kwargs
