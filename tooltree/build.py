from __future__ import annotations

import typing

from . import colors
from . import types

if typing.TYPE_CHECKING:
    import polars as pl
    from typing import Mapping


def create_treemap_data(
    df: pl.DataFrame,
    *,
    levels: list[str],
    metric: str,
    extra_metrics: list[str | pl.Expr] | None = None,
    metric_format: dict[str, typing.Any] | None = None,
    root: str = '',
    max_children: int | None = None,
    min_child_fraction: float | None = None,
    max_root_children: int | None = None,
    min_root_child_fraction: float | None = None,
    color_nodes: str | Mapping[str | tuple[str, ...], typing.Any] | None = None,
    color_agg: pl.Expr | None = None,
    color_root: str | None = None,
) -> types.TreemapData:
    import polars as pl

    # check inputs
    if len(df.filter(pl.col(metric) < 0)) > 0:
        raise Exception('metric column contains negative values')

    # base treemap data
    treemap_data: types.TreemapData = {
        'ids': [],
        'labels': [],
        'parents': [],
        'sizes': [],
        'tooltips': [],
        'total_size': df[metric].sum(),
        'metric': metric,
        'root': root,
        'node_colors': [] if color_nodes is not None else None,
    }

    # root node
    _add_treemap_entry(
        treemap_data=treemap_data,
        name=root,
        ancestors=None,
        parent_size=None,
        size=treemap_data['total_size'],
        metric_format=metric_format,
        entry=None,
        level=None,
        color_nodes=None,
        extra_metrics=None,
        color_root=color_root,
    )

    # level nodes
    children_count: dict[tuple[str, ...], int] = {}
    skipped: set[tuple[str, ...]] = set()
    sizes: dict[tuple[str, ...], int | float] = {(): treemap_data['total_size']}
    metric_aggs = _get_metric_agg(metric, extra_metrics, color_nodes, color_agg)
    for i, level in enumerate(levels):
        level_data = (
            df.group_by(*levels[: i + 1])
            .agg(**metric_aggs)
            .sort(metric, descending=True)
        )
        for entry in level_data.to_dicts():
            ancestors = tuple(entry[level] for level in levels[:i])
            if _should_skip_entry(
                ancestors=ancestors,
                children_count=children_count,
                df=df,
                entry=entry,
                i=i,
                max_children=max_children,
                max_root_children=max_root_children,
                metric=metric,
                min_child_fraction=min_child_fraction,
                min_root_child_fraction=min_root_child_fraction,
                sizes=sizes,
                skipped=skipped,
            ):
                skipped.add(ancestors + (entry[level],))
            else:
                _add_treemap_entry(
                    treemap_data=treemap_data,
                    name=entry[level],
                    ancestors=ancestors,
                    parent_size=sizes[ancestors],
                    size=entry[metric],
                    metric_format=metric_format,
                    entry=entry,
                    level=level,
                    color_nodes=color_nodes,
                    extra_metrics=extra_metrics,
                    color_root=color_root,
                )
                children_count.setdefault(ancestors, 0)
                children_count[ancestors] += 1
                sizes[ancestors + (entry[level],)] = entry[metric]

    return treemap_data


def _get_metric_agg(
    metric: str,
    extra_metrics: list[str | pl.Expr] | None = None,
    color_nodes: str | Mapping[str | tuple[str, ...], typing.Any] | None = None,
    color_agg: pl.Expr | None = None,
) -> dict[str, pl.Expr]:
    import polars as pl

    metric_aggs = {}
    for extra_metric in extra_metrics or []:
        if isinstance(extra_metric, str):
            metric_aggs[extra_metric] = pl.col(extra_metric).sum()
        elif isinstance(extra_metric, pl.Expr):
            metric_aggs[extra_metric.meta.output_name()] = extra_metric
        else:
            raise Exception('invalid extra_metric: ' + str(extra_metric))
    metric_aggs[metric] = pl.col(metric).sum()
    if isinstance(color_nodes, str) and color_nodes not in metric_aggs:
        if color_agg is not None:
            metric_aggs[color_nodes] = color_agg
        else:
            raise Exception(
                'if using custom color column, specify color_agg expr'
            )
    return metric_aggs


def _should_skip_entry(
    ancestors: tuple[str, ...],
    entry: dict[str, typing.Any],
    df: pl.DataFrame,
    i: int,
    metric: str,
    max_root_children: int | None,
    min_root_child_fraction: float | None,
    max_children: int | None,
    min_child_fraction: float | None,
    children_count: dict[tuple[str, ...], int],
    sizes: dict[tuple[str, ...], int | float],
    skipped: set[tuple[str, ...]],
) -> bool:
    if i == 0:
        if max_root_children is None:
            max_level_children = len(df) * 2
        else:
            max_level_children = max_root_children
        if min_root_child_fraction is None:
            min_level_child_fraction = 0.0
        else:
            min_level_child_fraction = min_root_child_fraction
    else:
        if max_children is None:
            max_level_children = len(df) * 2
        else:
            max_level_children = max_children
        if min_child_fraction is None:
            min_level_child_fraction = 0.0
        else:
            min_level_child_fraction = min_child_fraction

    # determine whether to skip entry
    if ancestors in skipped:
        return True
    if children_count.get(ancestors, 0) >= max_level_children:
        return True
    if (sizes[ancestors] == 0) or (
        entry[metric] / sizes[ancestors] < min_level_child_fraction
    ):
        return True
    return False


def _add_treemap_entry(
    treemap_data: types.TreemapData,
    *,
    name: str,
    ancestors: tuple[str, ...] | None,
    parent_size: int | float | None,
    size: int | float,
    metric_format: dict[str, typing.Any] | None,
    level: str | None,
    entry: dict[str, typing.Any] | None,
    color_nodes: str | Mapping[str | tuple[str, ...], typing.Any] | None,
    extra_metrics: list[str | pl.Expr] | None = None,
    color_root: str | None,
) -> None:
    # compute identifiers
    id = '__'.join((ancestors or ()) + (name,))
    label = _add_name_newlines(name, root=treemap_data['root'])
    if ancestors is None:
        parent_id = ''
    elif ancestors == ():
        parent_id = treemap_data['root']
    else:
        parent_id = '__'.join(ancestors)

    # create tooltip
    tooltip = _create_tooltip(
        name=label,
        ancestors=ancestors,
        parent_size=parent_size,
        size=size,
        treemap_data=treemap_data,
        metric_format=metric_format,
        entry=entry,
        extra_metrics=extra_metrics,
    )

    # compute color value
    color_value = colors._get_node_color(
        ancestors=ancestors,
        level=level,
        entry=entry,
        color_nodes=color_nodes,
        color_root=color_root,
    )

    # add to treemap data
    treemap_data['labels'].append(label)
    treemap_data['ids'].append(id)
    treemap_data['parents'].append(parent_id)
    treemap_data['sizes'].append(size)
    treemap_data['tooltips'].append(tooltip)
    if treemap_data['node_colors'] is not None:
        treemap_data['node_colors'].append(color_value)


def _add_name_newlines(name: str, root: str) -> str:
    if name is None:
        raise Exception('name is None')
    newline_exceptions: list[str] = []
    if name == root:
        return name
    if len(name) > 8 and name not in newline_exceptions:
        name = name.replace(' ', '<br>')
    if '<br>V' in name:
        name = name.replace('<br>V', ' V')
    return name


def _create_tooltip(
    name: str,
    ancestors: tuple[str, ...] | None,
    parent_size: int | float | None,
    size: int | float,
    treemap_data: types.TreemapData,
    metric_format: dict[str, typing.Any] | None,
    entry: dict[str, typing.Any] | None,
    extra_metrics: list[str | pl.Expr] | None = None,
) -> str:
    import toolstr

    tooltip = '<b>' + name.replace('<br>', ' ') + '</b>'

    # add size to tooltip
    if metric_format is None:
        metric_format = {}
    tooltip += ' ' + toolstr.format(size, **metric_format)

    # add percentage to tooltip
    fraction = size / treemap_data['total_size']
    fraction_str = toolstr.format(fraction, percentage=True, decimals=1)
    tooltip += '<br>' + fraction_str + ' of ' + treemap_data['metric']

    # add parent percentage to tooltip
    if (
        ancestors is not None
        and len(ancestors) >= 1
        and parent_size is not None
    ):
        as_str = toolstr.format(size / parent_size, percentage=True, decimals=1)
        tooltip += '<br>' + as_str + ' of ' + ancestors[-1]

    # add extra tooltip info
    if extra_metrics is not None and entry is not None:
        for column in extra_metrics:
            if isinstance(column, pl.Expr):
                extra_metric_name = column.meta.output_name()
            else:
                extra_metric_name = column
            if extra_metric_name not in entry:
                raise Exception(
                    f'extra_metric "{extra_metric_name}" not found in entry'
                )
            value_formatted = toolstr.format(
                entry[extra_metric_name],
                order_of_magnitude=True,
                decimals=1,
            )
            tooltip += '<br>' + value_formatted + ' ' + extra_metric_name

    return tooltip
