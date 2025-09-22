from __future__ import annotations

import typing

from . import types

if typing.TYPE_CHECKING:
    import polars as pl


def create_treemap_data(
    df: pl.DataFrame,
    *,
    levels: list[str],
    metric: str,
    extra_metrics: list[str | pl.Expr] | None = None,
    metric_format: dict[str, typing.Any] | None = None,
    root_name: str = '',
) -> types.TreemapData:
    """
    # Inputs
    - df: dataframe containing data to visualize
    - metric: column name to use for sizing
    - levels: list of column names to group by, in order of hierarchy
    """
    import polars as pl

    # base treemap data
    treemap_data: types.TreemapData = {
        'ids': [],
        'labels': [],
        'parents': [],
        'sizes': [],
        'customdata': [],
        'total_size': df[metric].sum(),
        'metric': metric,
        'root_name': root_name,
    }

    # metric aggregations
    metric_aggs = []
    for extra_metric in extra_metrics or []:
        if isinstance(extra_metric, str):
            metric_aggs.append(pl.col(extra_metric).sum())
        elif isinstance(extra_metric, pl.Expr):
            metric_aggs.append(extra_metric)
        else:
            raise Exception('invalid extra_metric: ' + str(extra_metric))
    extra_metric_names = [expr.meta.output_name() for expr in metric_aggs]
    metric_aggs.append(pl.col(metric).sum().alias(metric))

    # root node
    _add_treemap_entry(
        treemap_data=treemap_data,
        name=root_name,
        ancestors=[],
        size=treemap_data['total_size'],
        extra_tooltip_kwargs={},
        metric_format=metric_format,
    )

    # level nodes
    for i, level in enumerate(levels):
        level_data = df.group_by(*levels[: i + 1]).agg(*metric_aggs)
        for entry in level_data.to_dicts():
            _add_treemap_entry(
                treemap_data=treemap_data,
                name=entry[level],
                ancestors=[entry[level] for level in levels[:i]],
                size=entry[metric],
                extra_tooltip_kwargs={n: entry[n] for n in extra_metric_names},
                metric_format=metric_format,
            )

    return treemap_data


def _add_treemap_entry(
    treemap_data: types.TreemapData,
    *,
    name: str,
    ancestors: list[str],
    size: int | float,
    extra_tooltip_kwargs: dict[str, typing.Any] | None = None,
    metric_format: dict[str, typing.Any],
) -> None:
    import toolstr

    if name is None:
        raise Exception('name is None')

    name = _add_name_newlines(name, root_name=treemap_data['root_name'])
    ancestors = [
        _add_name_newlines(ancestor, root_name=treemap_data['root_name'])
        for ancestor in ancestors
    ]

    # determine unique id
    id = '__'.join(ancestors + [name])
    parent_id = '__'.join(ancestors)

    # create tooltip
    if metric_format is None:
        metric_format = {}
    item = (
        toolstr.format(size, **metric_format)
        + '<br>'
        + toolstr.format(
            size / treemap_data['total_size'], percentage=True, decimals=1
        )
        + ' of '
        + treemap_data['metric']
    )
    if extra_tooltip_kwargs is not None:
        for key, value in extra_tooltip_kwargs.items():
            item += (
                '<br>'
                + toolstr.format(value, order_of_magnitude=True, decimals=1)
                + ' '
                + key
            )

    treemap_data['ids'].append(id)
    treemap_data['labels'].append(name)
    treemap_data['parents'].append(parent_id)
    treemap_data['sizes'].append(size)
    treemap_data['customdata'].append(item)


def _add_name_newlines(name: str, root_name: str) -> str:
    newline_exceptions: list[str] = []
    if name == root_name:
        return name
    if len(name) > 8 and name not in newline_exceptions:
        name = name.replace(' ', '<br>')
    if '<br>V' in name:
        name = name.replace('<br>V', ' V')
    return name
