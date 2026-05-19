"""
Color-space helpers used by quantizers.

The quantizers operate on RGB arrays but can compute distances either directly
in RGB or in CIE Lab.  Lab is the default for image-to-pattern generation
because it is usually closer to perceived color difference.

Example::

    >>> import numpy as np
    >>> convert_colors(np.array([[255, 255, 255]], dtype=np.uint8), color_space="rgb").tolist()
    [[255.0, 255.0, 255.0]]
"""

from __future__ import annotations

from typing import Literal

import numpy as np
from skimage.color import rgb2lab

ColorSpace = Literal["rgb", "lab"]


def as_color_array(rgb: np.ndarray) -> np.ndarray:
    """
    Normalize an array-like RGB table to a ``float64`` ``(n, 3)`` array.

    :param rgb: RGB array-like object.
    :type rgb: numpy.ndarray
    :return: Normalized ``float64`` array.
    :rtype: numpy.ndarray
    :raises ValueError: If the input shape is not ``(n, 3)``.
    """

    arr = np.asarray(rgb, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError("Color array should have shape (n, 3).")
    return arr


def convert_colors(rgb: np.ndarray, color_space: ColorSpace = "lab") -> np.ndarray:
    """
    Convert RGB values in ``0..255`` to the requested distance space.

    :param rgb: RGB values with shape ``(n, 3)``.
    :type rgb: numpy.ndarray
    :param color_space: Target distance space, defaults to ``"lab"``.
    :type color_space: ColorSpace, optional
    :return: Converted color array.
    :rtype: numpy.ndarray
    :raises ValueError: If ``color_space`` is unsupported.
    """

    arr = as_color_array(rgb)
    if color_space == "rgb":
        return arr
    if color_space == "lab":
        return rgb2lab((arr / 255.0).reshape((-1, 1, 3))).reshape((-1, 3))
    raise ValueError(f"Unsupported color space: {color_space!r}.")
