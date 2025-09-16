from collections.abc import Mapping, Sequence

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap

from fancy_barchart.colormaps import resampled, ColorPairs, Style, Target
from fancy_barchart.util import alternate


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


def _colormap_by_bar_from(c: Chart, color_pairs: ColorPairs, pair_idx_by_category: Mapping[Name, int],
                          style_by_bar: Mapping[Name, Style]) -> dict[Name, dict[Name, ListedColormap]]:
    """
    For each bar in each group in ``Chart c``, create the appropriate colormap.

    :param c: chart to be colored
    :param color_pairs: available color pairs
    :param pair_idx_by_category: for each category name in the chart, the color pair to be used, as an index into the
        colormap of ``color_pairs``
    :param style_by_bar: for each bar name in the chart, the style to be used
    :return: {group name: {bar name: colormap}}
    """
    return {
        group_name: {
            bar_name: resampled({pair_idx_by_category[cat_name]: len(cat)}, color_pairs, style_by_bar[bar_name])
        } for group_name, group in c.items() for bar_name, bar in group.items() for cat_name, cat in bar.items()
    }


# TODO: Provide code for legend patches (with grouping options)


def chart(c: Chart, *, color_pairs: ColorPairs = ColorPairs(), pair_idxs: Sequence[int] | None = None,
          styles: Sequence[Style] | None = None, group_names: bool = True, bar_names: bool = True, legend: bool = True):
    """
    Create a grouped, stacked horizontal barchart with the following properties: (1) each group may consist of the same
    set of named bars, (2) each bar may consist of the same set of named categories, (3) each category may consist of
    multiple values, ultimately responsible for the bar's length, (4) each bar of the same name uses the same style, (5)
    each category of the same name uses the same color pair, (6) values within each category are colored with different
    shades of the category's color pair.

    :param c: ``{group name: {bar name: {category name: [values in category]}}}``
    :param color_pairs: available color pairs
    :param pair_idxs: indices of the color pairs used from ``color_pairs`` for coloring categories
        (default: None; i.e. use all color pairs, starting from index 0)
    :param styles: available styles for styling bars (default: None; i.e. alternate between ``HATCH`` and ``GRADIENT``)
    :param group_names: show each group's label/name (True; default) or not (False)
    :param bar_names: show each bar's label/name (True; default) or not (False)
    :param legend: show a legend of the colors and styles (True; default) or not (False)
    """
    all_groups = _all_groups_from(c)
    all_bars = _all_bars_from(c)
    all_categories = _all_categories_from(c)
    pair_idxs = range(len(all_categories)) if pair_idxs is None else pair_idxs
    if len(pair_idxs) < len(all_categories):
        raise ValueError(f"Got only {len(pair_idxs)} color pair indices for {len(all_categories)} categories.")
    styles = alternate(Style.HATCH, Style.GRADIENT, num=len(all_bars)) if styles is None else styles
    if len(styles) < len(all_bars):
        raise ValueError(f"Got only {len(styles)} styles for {len(all_bars)} bars.")
    # TODO: Continue here (1) create all colormaps (see above), (2) create groups (see
    #   https://matplotlib.org/stable/gallery/lines_bars_and_markers/barchart.html), (3) create grouped legends (see
    #   https://stackoverflow.com/questions/21570007/)
    all_colormaps = _colormap_by_bar_from(bars, all_categories, colors, cm)
    ax = plt.gca()
    ax.invert_yaxis()
    for (bar_name, bar_value), colormap in zip(bars.items(), all_colormaps):
        start, color_idx = 0, 0
        bar_colors = all_colormaps[bar_name].colors
        for category in all_categories:
            for value in bar_value.get(category, []):
                ax.barh(bar_name, value, color=bar_colors[color_idx], left=start)
                start += value
                color_idx += 1
    if not labels:
        ax.set_yticks([])
    # TODO: Reintegrate legend


if __name__ == "__main__":
    test = {
        "bar1": {"cat1": [1], "cat2": [3, 1, 5]},
        "bar2": {"cat1": [2, 1, 3], "cat3": [1, 1]}
    }
    cm = CM(map="Set1", unpaired=Target(color=(1, 1, 1), opacity=0.5))
    chart(test, colors=[0, 2, 3], cm=cm)