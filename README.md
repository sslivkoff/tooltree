
# tooltree

functions for creating treemap data visualizations

## Installation

```bash
uv add tooltree
```

## Example Usage

The main API is just one function, `tooltree.plot_treemap()`

See `tooltree.plot_treemap()` for full list of options

#### Basic Treemap

```python
import tooltree

tooltree.plot_treemap(
    df=dataframe,
    levels=[grandparent_column, parent_column, name_column],
    metric=metric_column,
    root='Root Node Name',
)
```

#### Output as HTML

```python
import tooltree

tooltree.plot_treemap(
    df=dataframe,
    levels=[grandparent_column, parent_column, name_column],
    metric=metric_column,
    root='Root Node Name',
    html_path='path/to/save/treemap.html',
)
```

#### Output as PNG

```python
import tooltree

tooltree.plot_treemap(
    df=dataframe,
    levels=[grandparent_column, parent_column, name_column],
    metric=metric_column,
    root='Root Node Name',
    png_path='path/to/save/treemap.png',
)
```

#### Limit Number of Treemap Children

```python
import tooltree

tooltree.plot_treemap(
    df=dataframe,
    levels=[grandparent_column, parent_column, name_column],
    metric=metric_column,
    root='Root Node Name',
    max_children=10,
    min_child_fraction=0.01,
    max_root_children=5,
    min_root_child_fraction=0.001,
)
```

#### Other Options

```python
import tooltree

tooltree.plot_treemap(
    df=dataframe,
    levels=[grandparent_column, parent_column, name_column],
    metric=metric_column,
    root='Root Node Name',
    metric_format=toolstr_kwargs,
    height=1600,
    width=1200,
)
```
