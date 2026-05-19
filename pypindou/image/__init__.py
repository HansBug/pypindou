"""
Image preprocessing and quantization APIs.

The image package contains low-level helpers used by
:func:`pypindou.pattern.generate_pattern`.  Most users should call the
high-level pattern API directly, while application code can import this package
to build custom preprocessing, quantization, and benchmarking flows.
"""

from .preprocess import (
    BackgroundMode,
    FitMode,
    PreprocessMode,
    ResampleMode,
    enhance_image,
    load_image,
    prefilter_image,
    remove_background_by_alpha,
    resize_image,
    rgba_to_rgb_array,
)
from .quantize import (
    CleanupMode,
    QuantizationResult,
    QuantizeMethod,
    cleanup_quantization,
    merge_small_regions,
    quantize_image,
    reduce_palette_for_image,
)

__all__ = [
    "BackgroundMode",
    "CleanupMode",
    "FitMode",
    "PreprocessMode",
    "QuantizationResult",
    "QuantizeMethod",
    "ResampleMode",
    "cleanup_quantization",
    "enhance_image",
    "load_image",
    "merge_small_regions",
    "prefilter_image",
    "quantize_image",
    "reduce_palette_for_image",
    "remove_background_by_alpha",
    "resize_image",
    "rgba_to_rgb_array",
]
