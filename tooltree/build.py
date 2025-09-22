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
    root: str = '',
    max_children: int | None = None,
    min_child_fraction: float | None = None,
    max_root_children: int | None = None,
    min_root_child_fraction: float | None = None,
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
        'root': root,
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
        name=root,
        ancestors=None,
        parent_size=None,
        size=treemap_data['total_size'],
        extra_tooltip_kwargs={},
        metric_format=metric_format,
    )

    # level nodes
    children_count: dict[tuple[str, ...], int] = {}
    skipped: set[tuple[str, ...]] = set()
    sizes: dict[tuple[str, ...], int | float] = {(): treemap_data['total_size']}
    for i, level in enumerate(levels):
        level_data = (
            df.group_by(*levels[: i + 1])
            .agg(*metric_aggs)
            .sort(metric, descending=True)
        )
        for entry in level_data.to_dicts():
            ancestors = tuple(entry[level] for level in levels[:i])

            # determine whether to skip entry
            if _should_skip_entry(
                ancestors=ancestors,
                children_count=children_count,
                df=df,
                entry=entry,
                i=i,
                level=level,
                max_children=max_children,
                max_root_children=max_root_children,
                metric=metric,
                min_child_fraction=min_child_fraction,
                min_root_child_fraction=min_root_child_fraction,
                sizes=sizes,
                skipped=skipped,
            ):
                skipped.add(ancestors + (entry[level],))
                continue

            # add entry
            _add_treemap_entry(
                treemap_data=treemap_data,
                name=entry[level],
                ancestors=ancestors,
                parent_size=sizes[ancestors],
                size=entry[metric],
                extra_tooltip_kwargs={n: entry[n] for n in extra_metric_names},
                metric_format=metric_format,
            )

            # record stats
            children_count.setdefault(ancestors, 0)
            children_count[ancestors] += 1
            sizes[ancestors + (entry[level],)] = entry[metric]

    return treemap_data


def _should_skip_entry(
    ancestors: tuple[str, ...],
    entry: dict[str, typing.Any],
    df: pl.DataFrame,
    i: int,
    level: str,
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
    extra_tooltip_kwargs: dict[str, typing.Any] | None,
    metric_format: dict[str, typing.Any] | None,
) -> None:
    import toolstr

    if name is None:
        raise Exception('name is None')

    name = _add_name_newlines(name, root=treemap_data['root'])
    if ancestors is None:
        ancestors = typing.cast(tuple[str, ...], ())
    else:
        ancestors = (treemap_data['root'],) + tuple(
            _add_name_newlines(ancestor, root=treemap_data['root'])
            for ancestor in ancestors
        )

    # determine unique id
    id = '__'.join(ancestors + (name,))
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

    # add in parent
    if len(ancestors) > 1 and parent_size is not None:
        item += (
            '<br>'
            + toolstr.format(size / parent_size, percentage=True, decimals=1)
            + ' of '
            + ancestors[-1]
        )

    # extra tooltip info
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


def _add_name_newlines(name: str, root: str) -> str:
    newline_exceptions: list[str] = []
    if name == root:
        return name
    if len(name) > 8 and name not in newline_exceptions:
        name = name.replace(' ', '<br>')
    if '<br>V' in name:
        name = name.replace('<br>V', ' V')
    return name
