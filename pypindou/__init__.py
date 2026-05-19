"""
pypindou - image-to-fuse-bead pattern generation.
"""

from .color import BeadColor, Palette, get_palette, list_palettes, load_palette
from .config.meta import __VERSION__ as __version__
from .pattern import Pattern, PatternOptions, generate_pattern

__all__ = [
    "__version__",
    "BeadColor",
    "Palette",
    "Pattern",
    "PatternOptions",
    "generate_pattern",
    "get_palette",
    "list_palettes",
    "load_palette",
]
