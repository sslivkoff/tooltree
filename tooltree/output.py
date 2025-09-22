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
    root_name: str = '',
    #
    # visualization
    colors: list[str] | None = None,
    height: int | None = None,
    #
    # output
    output: types.OutputFormat | None = None,
    output_path: str | None = None,
) -> types.TreemapPlot:
    treemap_data = build.create_treemap_data(
        df,
        metric=metric,
        levels=levels,
        extra_metrics=extra_metrics,
        root_name=root_name,
    )
    fig = visualize.create_treemap_figure(
        treemap_data=treemap_data,
    )
    output_figure(
        fig=fig,
        output=output,
        output_path=output_path,
    )

    return {
        'data': treemap_data,
        'fig': fig,
        'output_path': output_path,
    }


def show_figure(fig: go.Figure) -> None:
    fig.show(config={'displayModeBar': False})


def export_figure_to_html(fig: go.Figure, output_path: str) -> None:
    fig.write_html(output_path, config={'displayModeBar': False})
    # fig.write_html(output_path, include_plotlyjs='cdn', full_html=True)


def output_figure(
    fig: go.Figure, output: types.OutputFormat | None, output_path: str | None
) -> None:
    if output is None:
        if output_path is not None:
            output = 'html'
        else:
            output = 'show'
    outputs = []
    if output == 'show':
        outputs.append('show')
    elif output == 'html':
        outputs.append('html')
    elif isinstance(output, list):
        outputs = output
    else:
        raise Exception('invalid output')
    if 'show' in outputs:
        show_figure(fig)
    if 'html' in outputs:
        if output_path is None:
            raise Exception('set output_path to file path')
        print('writing treemap output to', output_path)
        export_figure_to_html(fig, output_path=output_path)
