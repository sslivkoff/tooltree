from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    import plotly.graph_objects as go  # type: ignore


OutputFormat = typing.Literal['show', 'html']


class TreemapData(typing.TypedDict):
    metric: str
    root: str
    total_size: int | float
    ids: list[str]
    labels: list[str]
    parents: list[str | None]
    sizes: list[int | float]
    customdata: list[str]


class TreemapPlot(typing.TypedDict):
    data: TreemapData
    fig: go.Figure
    html_path: str | None
    png_path: str | None
