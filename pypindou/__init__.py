"""
Pure Python image-to-fuse-bead pattern generation.

``pypindou`` exposes the stable public API for loading built-in bead palettes
and generating :class:`pypindou.pattern.Pattern` objects from images.  Lower
level image preprocessing and quantization helpers remain available from their
subpackages for applications that need custom workflows.

Example::

    >>> from PIL import Image
    >>> from pypindou import generate_pattern
    >>> pattern = generate_pattern(Image.new("RGB", (2, 2), "white"), width=2, height=2, color_space="rgb")
    >>> pattern.bead_count
    4
"""

from .color import BeadColor, Palette, get_palette, list_palettes, load_palette
from .config.meta import __VERSION__ as __version__
from .pattern import Pattern, PatternOptions, SymbolFormat, SymbolLabelMode, generate_pattern

__all__ = [
    "__version__",
    "BeadColor",
    "Palette",
    "Pattern",
    "PatternOptions",
    "SymbolFormat",
    "SymbolLabelMode",
    "generate_pattern",
    "get_palette",
    "list_palettes",
    "load_palette",
]
