from collections.abc import Mapping, Sequence
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from matplotlib.colors import ListedColormap
from colormaps import resampled, CM, Target

Name, Value = str, float
Category = Sequence[Value]
Bar = Mapping[Name, Category]
Group = Mapping[Name, Bar]
Chart = Mapping[Name, Group]


def _all_groups_from(c: Chart) -> list[Name]:
    """Return unique group names of ``Chart c``, in order of their appearance."""
    return list(c)


def _all_bars_from(c: Chart) -> list[Name]:
    """Return unique bar names of ``Chart c``, in order of their appearance."""
    return list(dict.fromkeys(bar for group in c.values() for bar in group))  # ``dict.fromkeys()`` to preserve order


def _all_categories_from(c: Chart) -> list[Name]:
    """Return unique category names of ``Chart c``, in order of their appearance."""
    return list(dict.fromkeys(cat for group in c.values() for bar in group.values() for cat in bar))
