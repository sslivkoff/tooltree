from __future__ import annotations


import typing


class TreemapData(typing.TypedDict):
    metric: str
    root_name: str
    total_size: int | float
    names: list[str]
    parents: list[str | None]
    sizes: list[int | float]
    customdata: list[str]
