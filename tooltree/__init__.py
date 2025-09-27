"""functions for creating treemap data visualizations"""

__version__ = '0.1.1'

import typing
from .output import plot_treemap

if typing.TYPE_CHECKING:
    from .types import TreemapData, TreemapPlot
