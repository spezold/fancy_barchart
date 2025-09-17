from collections.abc import Sequence
from dataclasses import dataclass

from matplotlib.colors import ListedColormap
from matplotlib.legend import Legend
from matplotlib.image import BboxImage
from matplotlib.transforms import TransformedBbox, Bbox
import numpy as np

from fancy_barchart.colormaps import Color, Style


@dataclass(frozen=True, kw_only=True)
class FancyHandle:
    rgb_src: Color
    """Source color (RGB in [0., 1.])"""
    rgb_dst: Color
    """Destination color (RGB in [0., 1.])"""
    styles: Sequence[Style]
    """Styles to be stacked in the handle"""
    num: Sequence[int] | None = None
    """For each style, the number of steps to use (default: 100 for ``GRADIENT``, 5 for ``HATCH``)"""
    label: str = ""
    """Label for the handle in the legend (default: "")"""

    def __post_init__(self):
        # https://stackoverflow.com/a/54119384/7395592 (20250917)
        object.__setattr__(self, "styles", tuple(self.styles))
        num = tuple(({Style.GRADIENT: 100, Style.HATCH: 5}[s] for s in self.styles) if self.num is None else self.num)
        object.__setattr__(self, "num", num)

    def get_label(self): return self.label  # Used in ``matplotlib.pyplot.legend()``

    def __len__(self): return len(self.styles)

    def __getitem__(self, key) -> ListedColormap:
        return ListedColormap(self.styles[key].value(self.rgb_src, self.rgb_dst, self.num[key]))


class FancyHandler:
    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        # https://matplotlib.org/stable/api/legend_handler_api.html#matplotlib.legend_handler.HandlerBase.legend_artist
        x, y, w, h, t = (b := handlebox).xdescent, b.ydescent, b.width, b.height / len(orig_handle), b.get_transform()

        for i, cm in enumerate(reversed(orig_handle)):
            # For each style's colormap, place a tiny gradient image (https://stackoverflow.com/a/42971319/7395592) into
            # the legend (https://stackoverflow.com/a/32303541/7395592), then apply colormap (start from bottom up)
            bbox = TransformedBbox(Bbox.from_bounds(x, y + i * h, w, h), transform=t)
            img = BboxImage(bbox, cmap=cm, interpolation="nearest")
            img.set_data(np.linspace(0, 1, num=len(cm.colors))[np.newaxis])
            handlebox.add_artist(img)
        return handlebox


Legend.update_default_handler_map({FancyHandle: FancyHandler()})  # Globally register ``FancyHandler``
