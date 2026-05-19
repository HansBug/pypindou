"""
Color-space helpers used by quantizers.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
from skimage.color import rgb2lab

ColorSpace = Literal["rgb", "lab"]


def as_color_array(rgb: np.ndarray) -> np.ndarray:
    """
    Normalize an array-like RGB table to a ``float64`` ``(n, 3)`` array.
    """

    arr = np.asarray(rgb, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError("Color array should have shape (n, 3).")
    return arr


def convert_colors(rgb: np.ndarray, color_space: ColorSpace = "lab") -> np.ndarray:
    """
    Convert RGB values in ``0..255`` to the requested distance space.
    """

    arr = as_color_array(rgb)
    if color_space == "rgb":
        return arr
    if color_space == "lab":
        return rgb2lab((arr / 255.0).reshape((-1, 1, 3))).reshape((-1, 3))
    raise ValueError(f"Unsupported color space: {color_space!r}.")
