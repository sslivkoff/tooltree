from __future__ import annotations

import typing
from . import build
from . import defaults
from . import types
from . import visualize

if typing.TYPE_CHECKING:
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
    colors: list[str] | None = None,
    height: int | None = None,
    width: int | None = None,
    #
    # output
    output: types.OutputFormat | None = None,
    html_path: str | None = None,
    png_path: str | None = None,
) -> types.TreemapPlot:
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
    )
    fig = visualize.create_treemap_figure(
        treemap_data=treemap_data,
        height=height,
        width=width,
        colors=colors,
    )
    output_figure(
        fig=fig,
        output=output,
        html_path=html_path,
        png_path=png_path,
        height=height,
        width=width,
    )
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


def output_figure(
    fig: go.Figure,
    output: types.OutputFormat | None,
    html_path: str | None,
    png_path: str | None,
    height: int | None = None,
    width: int | None = None,
) -> None:
    # determine output format
    outputs = []
    if output is None:
        if html_path is not None:
            outputs.append('html')
        if png_path is not None:
            outputs.append('png')
        if len(outputs) == 0:
            outputs.append('show')
    if output in ['show', 'png', 'html']:
        outputs.append(output)
    elif isinstance(output, list):
        outputs = output
    elif len(outputs) == 0:
        raise Exception('invalid output')

    # create outputs
    if 'show' in outputs:
        show_figure(fig)
    if 'html' in outputs:
        if html_path is None:
            raise Exception('set html_path to file path')
        print('writing treemap html to', html_path)
        export_figure_to_html(fig, html_path=html_path)
    if 'png' in outputs:
        if png_path is None:
            raise Exception('set output_path to file path')
        print('writing treemap png to', png_path)
        export_figure_to_png(fig, png_path=png_path, height=height, width=width)
