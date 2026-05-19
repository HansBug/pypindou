"""
Color palettes and color-space utilities.

This package provides the palette dataclasses, RGB/hex conversion helpers,
packaged palette loading, and color-space conversion used by quantizers.

Example::

    >>> from pypindou.color import hex_to_rgb, rgb_to_hex
    >>> rgb_to_hex(hex_to_rgb("#FFFFFF"))
    '#FFFFFF'
"""

from .model import BeadColor, Palette, RGB, hex_to_rgb, rgb_to_hex
from .resources import get_palette, list_palettes, load_palette
from .space import ColorSpace, convert_colors

__all__ = [
    "BeadColor",
    "ColorSpace",
    "Palette",
    "RGB",
    "convert_colors",
    "get_palette",
    "hex_to_rgb",
    "list_palettes",
    "load_palette",
    "rgb_to_hex",
]
