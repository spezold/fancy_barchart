from collections.abc import Mapping, Sequence

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np

from fancy_barchart.colormaps import resampled, ColorPairs, Style, Target
from fancy_barchart.legend import FancyHandle
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
    steps = lambda bar: {pair_idx_by_category[cat_name]: len(cat) for cat_name, cat in bar.items()}
    resampled_bar = lambda bar_name, bar: resampled(steps(bar), color_pairs, style_by_bar[bar_name])
    return {gn: {bn: resampled_bar(bn, bar) for bn, bar in group.items()} for gn, group in c.items()}


def _handles_from(styles: Sequence[Style], color_pairs: ColorPairs, pair_idx_by_category: Mapping[Name, int])\
        -> list[FancyHandle]:
    """
    For each category, create an appropriate legend handle.

    :param styles: all styles used in the chart
    :param color_pairs: available color pairs
    :param pair_idx_by_category: for each category name in the chart, the color pair to be used, as an index into the
        colormap of ``color_pairs``
    """
    handles = []
    styles = styles[:2]  # Show the first two styles max.
    for cat, pair_idx in pair_idx_by_category.items():
        rgb_src, rgb_dst = color_pairs.values[2 * pair_idx], color_pairs.values[2 * pair_idx + 1]
        handles.append(FancyHandle(rgb_src=tuple(rgb_src), rgb_dst=tuple(rgb_dst), styles=styles, label=cat))
    return handles


def chart(c: Chart, *, color_pairs: ColorPairs = ColorPairs(), pair_idxs: Sequence[int] | None = None,
          styles: Sequence[Style] | None = None, group_names: bool = True, bar_names: bool = True, legend: bool = True):
    """
    Create a grouped, stacked horizontal barchart with the following properties: (1) each group may consist of the same
    set of named bars, (2) each bar may consist of the same set of named categories, (3) each category may consist of
    multiple values, ultimately responsible for the bar's length, (4) each bar of the same name uses the same style, (5)
    each category of the same name uses the same color pair, (6) values within each category are colored with different
    shades of the category's color pair.

    :param c: dictionary describing the chart: ``{group name: {bar name: {category name: [values in category]}}}``
    :param color_pairs: available color pairs
    :param pair_idxs: indices of the color pairs used from ``color_pairs`` for coloring categories
        (default: None; i.e. use all color pairs, starting from index 0)
    :param styles: available styles for styling bars (default: None; i.e. alternate between ``HATCH`` and ``GRADIENT``)
    :param group_names: show each group's label/name (True; default) or not (False)
    :param bar_names: show each bar's label/name (True; default) or not (False)
    :param legend: show a legend of the colors and styles (True; default) or not (False)
    """
    all_bars = _all_bars_from(c)
    all_categories = _all_categories_from(c)
    pair_idxs = range(len(all_categories)) if pair_idxs is None else pair_idxs
    if len(pair_idxs) < len(all_categories):
        raise ValueError(f"Got only {len(pair_idxs)} color pair indices for {len(all_categories)} categories.")
    styles = alternate(Style.HATCH, Style.GRADIENT, num=len(all_bars)) if styles is None else styles
    if len(styles) < len(all_bars):
        raise ValueError(f"Got only {len(styles)} styles for {len(all_bars)} bars.")
    pair_idx_by_category = dict(zip(all_categories, pair_idxs))
    style_by_bar = dict(zip(all_bars, styles))
    all_colormaps = _colormap_by_bar_from(c, color_pairs, pair_idx_by_category, style_by_bar)
    # TODO: (3) create grouped legends (see https://stackoverflow.com/questions/21570007/)
    ax = plt.gca()
    ax.invert_yaxis()
    bar_w = .8 / len(all_bars)  # Use default width and distribute among bars in group
    for g, (group_name, group) in enumerate(c.items()):
        for b, bar_name in enumerate(all_bars):  # Iterate over `all_bars` to allow for missing bars in group
            cont = None
            if bar := group.get(bar_name):
                colors = all_colormaps[group_name][bar_name].colors
                start, color_i = 0, 0
                for cat_name in all_categories:  # Iterate over `all_categories` to allow for missing categories in bar
                    for val in bar.get(cat_name, []):
                        cont = ax.barh(g + bar_w * b, val, bar_w, color=colors[color_i], left=start, label=bar_name)
                        start += val
                        color_i += 1
            if bar_names:
                # Create empty container for empty or missing bars, then add label
                cont = ax.barh(g + bar_w * b, 0, bar_w, left=0, label=bar_name) if cont is None else cont
                ax.bar_label(cont, padding=3, labels=[bar_name])
    ax.set_yticks(*(np.arange(len(c)) + (len(all_bars) - 1) / 2 * bar_w, c.keys()) if group_names else [])
    if legend:
        all_handles = _handles_from(styles, color_pairs, pair_idx_by_category)
        plt.legend(handles=all_handles)


if __name__ == "__main__":
    test = {
        "bar1": {"cat1": [1], "cat2": [3, 1, 5]},
        "bar2": {"cat1": [2, 1, 3], "cat3": [1, 1]}
    }
    cm = CM(map="Set1", unpaired=Target(color=(1, 1, 1), opacity=0.5))
    chart(test, colors=[0, 2, 3], cm=cm)