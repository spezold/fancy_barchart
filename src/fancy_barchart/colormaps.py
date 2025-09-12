from typing import Literal, NamedTuple
from warnings import warn

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, to_rgb
import numpy as np
from numpy.typing import NDArray
try:
    from skimage.color import rgb2lab, lab2rgb
except ImportError as ie:
    warn(f"Could not import module '{ie.name}' to interpolate in CIELAB space, use RGB space instead.", UserWarning)
    rgb2lab = lab2rgb = lambda img: img


class Target(NamedTuple):
    """Determine to what extent and with which (global) target color each color from the colormap is paired."""
    color: str | NDArray[float] = "white"
    """target value for pairing (color name or RGB tuple)"""
    opacity: float = 0.5
    """opacity of the target value: the actual target is produced as ``(1 - opacity) * src + opacity * target``)"""


class CM(NamedTuple):
    """Determine the colormap and resampling strategy to be used."""
    map: str | ListedColormap = "tab20"
    """matplotlib colormap or its name to be used (should be a ``ListedColormap``, usually a qualitative one)"""
    mode: Literal["interpolate", "alternate"] = "interpolate"
    """either "interpolate" (linearly interpolate each color pair) or "alternate" (alternate each pair's colors)"""
    unpaired: Target | None = None
    """assume successive colors as paired if None, else create a paired value for each color by the given parameters"""


def interpolate(rgb1: NDArray[float], rgb2: NDArray[float], steps: int) -> NDArray[float]:
    """
    Linearly interpolate from ``rgb1`` to ``rgb2`` over the given number of ``steps`` in CIELAB color space, return the
    corresponding ``steps×3`` RGB array (assert and return values in range 0.,…,1.).
    """
    lab = lambda rgb: rgb2lab(np.asarray(rgb).reshape(1, -1)).flatten()
    return np.clip(lab2rgb(np.linspace(lab(rgb1), lab(rgb2), steps)), 0, 1)


def alternate(rgb1: NDArray[float], rgb2: NDArray[float], steps: int) -> NDArray[float]:
    """Alternate ``rgb1`` and ``rgb2`` as often as necessary, return the corresponding ``steps×3`` array."""
    return np.array(([rgb1, rgb2] * ((steps + 1) // 2))[:steps])


def unpaired_target(rgb1: NDArray[float], rgb2: NDArray[float], opacity: float) -> NDArray[float]:
    """
    From the given source color(s) ``rgb1`` (N×3 or 3-tuple), linearly interpolate to the given target color(s) ``rgb2``
    (N×3 or 3-tuple) in CIELAB color space, by ``(1 - opacity) * rgb1 + opacity * rgb2``; return the corresponding
    ``N×3`` array containing the actual target color(s) in RGB space (assert and return values in range 0.,…,1.).
    """
    lab = lambda rgb_: rgb2lab(np.asarray(rgb_).reshape(-1, 3))
    rgb = lambda lab_: np.clip(lab2rgb(np.asarray(lab_).reshape(-1, 3)), 0, 1)
    return rgb((1 - opacity) * lab(rgb1) + opacity * lab(rgb2))


def paired(colors: NDArray[float], target: Target) -> NDArray[float]:
    """
    For all given RGB source ``colors`` (N×3 array), produce the corresponding target colors according to ``target``,
    interleave source and target colors, return the corresponding 2N×3 array (assert and return values in range
    0.,…,1.).
    """
    colors = np.asarray(colors)
    paired_colors = unpaired_target(colors, np.asarray(to_rgb(target.color)), opacity=target.opacity)
    # Interleave
    result = np.empty((2 * colors.shape[0], colors.shape[1]))
    result[::2] = colors
    result[1::2] = paired_colors
    return result


def resampled(steps: list[int] | dict[int, int], cm: CM = CM()) -> ListedColormap:
    """
    Resample a colormap, so that each color (or color pair) is extended to its corresponding number of ``steps``.

    :param steps: value at index ``i`` (list) or key ``i`` (dict) indicates that the ``i``-th color (or color pair)
        should be extended to the corresponding number of ``steps``
    :param cm: colormap properties
    :return: resampled colormap
    """
    if cm.mode not in (modes := {"interpolate", "alternate"}):
        raise ValueError(f"Unknown {cm.mode=} (need {', '.join(sorted(modes))}).")
    compose = interpolate if cm.mode == "interpolate" else alternate
    cmap = plt.get_cmap(cm.map) if isinstance(cm.map, str) else cm.map
    if not isinstance(cmap, ListedColormap):
        raise ValueError(f"Expected 'cm.map' as ListedColormap, got {cmap.__class__} instead.")
    colors = cmap.colors
    if cm.unpaired is not None:  # Pair colors if necessary (assume them as already paired and interleaved otherwise)
        colors = paired(colors, target=cm.unpaired)
    if (num_given := len(colors) // 2) < (num_needed := (max(steps) + 1 if isinstance(steps, dict) else len(steps))):
        raise ValueError(f"Need {num_needed}, but given colormap provides only {num_given} colors (or color pairs).")
    if isinstance(steps, dict):  # Extract colors at given indices if necessary
        colors = [colors[ci] for si in steps.keys() for ci in (2 * si, 2 * si + 1)]
        steps = steps.values()
    chunks = [compose(c1, c2, s) for c1, c2, s in zip(colors[::2], colors[1::2], steps) if s != 0]
    return ListedColormap(np.vstack(chunks))    
