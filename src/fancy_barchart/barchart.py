from collections.abc import Mapping, Sequence
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from matplotlib.colors import ListedColormap
from colormaps import resampled, ColorPairs, Style, Target

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


def _colormap_by_bar_from(c: Chart, color_pairs: ColorPairs, color_pair_by_category: Mapping[Name, int],
                          style_by_bar: Mapping[Name, Style]) -> dict[Name, dict[Name, ListedColormap]]:
    """
    For each bar in each group in ``Chart c``, create the appropriate colormap.

    :param c: chart to be colored
    :param color_pairs: available color pairs
    :param color_pair_by_category: for each category name in the chart, the color pair to be used, as an index into the
        colormap of ``color_pairs``
    :param style_by_bar: for each bar name in the chart, the style to be used
    :return: {group name: {bar name: colormap}}
    """
    return {
        group_name: {
            bar_name: resampled({color_pair_by_category[cat_name]: len(cat)}, color_pairs, style_by_bar[bar_name])
        } for group_name, group in c.items() for bar_name, bar in group.items() for cat_name, cat in bar.items()
    }
