from __future__ import annotations

import typing
from . import build
from . import defaults
from . import types
from . import visualize

if typing.TYPE_CHECKING:
    from typing import Mapping
    import polars as pl
    import plotly.graph_objects as go  # type: ignore


def plot_treemap(
    df: pl.DataFrame,
    *,
    #
    # treemap data
    levels: list[str],
    metric: str,
    extra_metrics: list[str | pl.Expr] | None = None,
    root: str = '',
    metric_format: dict[str, typing.Any] | None = None,
    max_children: int | None = None,
    min_child_fraction: float | None = None,
    max_root_children: int | None = None,
    min_root_child_fraction: float | None = None,
    #
    # visualization
    height: int | None = None,
    width: int | None = None,
    max_depth: int | None = None,
    treemap_object_kwargs: dict[str, typing.Any] | None = None,
    trace_kwargs: dict[str, typing.Any] | None = None,
    layout_kwargs: dict[str, typing.Any] | None = None,
    color_branches: list[str] | dict[str, str | None] | None = None,
    color_nodes: str | Mapping[str | tuple[str, ...], typing.Any] | None = None,
    color_agg: pl.Expr | None = None,
    color_root: str | None = None,
    cmap: str | None = None,
    cmin: int | float | None = None,
    cmid: int | float | None = None,
    cmax: int | float | None = None,
    color_bar: bool = False,
    #
    # output
    show: bool | None = None,
    html_path: str | None = None,
    png_path: str | None = None,
) -> types.TreemapPlot:
    """
    Specifying color:
    - [Color: str | int | float]
        - if numerical, use color scale
        - if str, interpret as color (e.g. 'red', '#ff0000', 'rgb(255, 0, 0)')
    1. color_branches: list[ColorStr | None]
        - list of colors for toplevel branches
    2. color_branches: dict[str, ColorStr | None]
        - map from branch name to color, root branches only
    3. color_nodes: str
        - column name of node color values
    4. color_nodes: dict[str | tuple[str, ...], Color | None]
        - map from node name to color
    """
    treemap_data = build.create_treemap_data(
        df,
        metric=metric,
        levels=levels,
        extra_metrics=extra_metrics,
        root=root,
        metric_format=metric_format,
        max_children=max_children,
        min_child_fraction=min_child_fraction,
        max_root_children=max_root_children,
        min_root_child_fraction=min_root_child_fraction,
        color_nodes=color_nodes,
        color_agg=color_agg,
        color_root=color_root,
    )
    fig = visualize.create_treemap_figure(
        treemap_data=treemap_data,
        metric=metric,
        height=height,
        width=width,
        max_depth=max_depth,
        treemap_object_kwargs=treemap_object_kwargs,
        trace_kwargs=trace_kwargs,
        layout_kwargs=layout_kwargs,
        color_branches=color_branches,
        color_nodes=color_nodes,
        color_root=color_root,
        cmap=cmap,
        cmin=cmin,
        cmid=cmid,
        cmax=cmax,
        color_bar=color_bar,
    )

    # output figure
    if show is None:
        show = html_path is None and png_path is None
    if show:
        show_figure(fig)
    if html_path is not None:
        if html_path is None:
            raise Exception('set html_path to file path')
        print('writing treemap html to', html_path)
        export_figure_to_html(fig, html_path=html_path)
    if png_path is not None:
        if png_path is None:
            raise Exception('set output_path to file path')
        print('writing treemap png to', png_path)
        export_figure_to_png(fig, png_path=png_path, height=height, width=width)

    # print summary
    print_treemap_stats(treemap_data)

    return {
        'data': treemap_data,
        'fig': fig,
        'html_path': html_path,
        'png_path': png_path,
    }


def print_treemap_stats(treemap_data: types.TreemapData) -> None:
    pass


def show_figure(fig: go.Figure) -> None:
    fig.show(config={'displayModeBar': False})


def export_figure_to_html(fig: go.Figure, html_path: str) -> None:
    import os

    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    fig.write_html(html_path, config={'displayModeBar': False})
    # fig.write_html(output_path, include_plotlyjs='cdn', full_html=True)


def export_figure_to_png(
    fig: go.Figure,
    png_path: str,
    scale: int = 4,
    height: int | None = None,
    width: int | None = None,
) -> None:
    import os

    os.makedirs(os.path.dirname(png_path), exist_ok=True)

    if height is None:
        height = defaults.default_png_height
    if width is None:
        width = defaults.default_png_width
    if scale is None:
        scale = defaults.default_png_scale
    fig.write_image(
        png_path, format='png', scale=scale, width=width, height=height
    )
