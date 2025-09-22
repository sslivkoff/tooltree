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
        parent=None,
        size=treemap_data['total_size'],
        extra_tooltip_kwargs={},
    )

    # level nodes
    for i, level in enumerate(levels):
        level_data = df.group_by(*levels[: i + 1]).agg(*metric_aggs)
        for entry in level_data.to_dicts():
            if i == 0:
                parent = root_name
            else:
                parent = entry[levels[i - 1]]

            _add_treemap_entry(
                treemap_data=treemap_data,
                name=entry[level],
                parent=parent,
                size=entry[metric],
                extra_tooltip_kwargs={n: entry[n] for n in extra_metric_names},
            )

    return treemap_data


def _add_treemap_entry(
    treemap_data: types.TreemapData,
    *,
    name: str,
    parent: str | None,
    size: int | float,
    extra_tooltip_kwargs: dict[str, typing.Any] | None = None,
) -> None:
    import toolstr

    if name is None:
        raise Exception('name is None')

    name = _add_name_newlines(name, root_name=treemap_data['root_name'])
    if parent is not None:
        parent = _add_name_newlines(parent, root_name=treemap_data['root_name'])

    # determine unique id
    id = name
    if parent is not None and id in treemap_data['ids']:
        id = parent + '_' + id
    if id in treemap_data['ids']:
        for i in range(2, 1000):
            candidate = id + '_' + str(i)
            if candidate not in treemap_data['ids']:
                id = candidate
                break
        else:
            raise Exception('could not determine unique id for ' + name)

    # create tooltip
    item = (
        toolstr.format(int(size), decimals=1)
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
    treemap_data['parents'].append(parent)
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
