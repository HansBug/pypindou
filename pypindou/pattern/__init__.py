"""
Pattern generation and rendering APIs.

Import from this package when an application needs to generate structured bead
patterns or render preview/symbol images from an existing
:class:`pypindou.pattern.Pattern`.
"""

from .generate import PatternOptions, generate_pattern, generate_pattern_with_options
from .model import Pattern, SymbolFormat, SymbolLabelMode, color_for_code

__all__ = [
    "Pattern",
    "PatternOptions",
    "SymbolFormat",
    "SymbolLabelMode",
    "color_for_code",
    "generate_pattern",
    "generate_pattern_with_options",
]
