"""
High-level image-to-pattern generation API.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Union

from PIL import Image

from pypindou.color import ColorSpace, Palette, get_palette
from pypindou.image import (
    BackgroundMode,
    FitMode,
    QuantizeMethod,
    ResampleMode,
    load_image,
    quantize_image,
    reduce_palette_for_image,
    remove_background_by_alpha,
    resize_image,
    rgba_to_rgb_array,
)

from .model import Pattern


@dataclass(frozen=True)
class PatternOptions:
    """
    Options for :func:`generate_pattern`.
    """

    width: int
    height: int
    palette: Union[str, Palette] = "mard-221-alfonse-doudou"
    fit: FitMode = "contain"
    background: BackgroundMode = "white"
    alpha_threshold: int = 16
    resample: ResampleMode = "lanczos"
    color_space: ColorSpace = "lab"
    quantize: QuantizeMethod = "nearest"
    max_colors: Optional[int] = None
    include_codes: Optional[Tuple[str, ...]] = None
    exclude_codes: Optional[Tuple[str, ...]] = None
    allow_unidentified: bool = False
    random_state: int = 0


def generate_pattern(
    image: Union[str, Path, Image.Image],
    *,
    width: int,
    height: int,
    palette: Union[str, Palette] = "mard-221-alfonse-doudou",
    fit: FitMode = "contain",
    background: BackgroundMode = "white",
    alpha_threshold: int = 16,
    resample: ResampleMode = "lanczos",
    color_space: ColorSpace = "lab",
    quantize: QuantizeMethod = "nearest",
    max_colors: Optional[int] = None,
    include_codes: Optional[Tuple[str, ...]] = None,
    exclude_codes: Optional[Tuple[str, ...]] = None,
    allow_unidentified: bool = False,
    random_state: int = 0,
) -> Pattern:
    """
    Generate a fuse-bead pattern from an input image.
    """

    src = load_image(image)
    src = remove_background_by_alpha(src, alpha_threshold=alpha_threshold)
    resized = resize_image(src, (width, height), fit=fit, resample=resample)
    rgb, active = rgba_to_rgb_array(resized, background=background, alpha_threshold=alpha_threshold)

    base_palette = get_palette(
        palette,
        include_codes=include_codes,
        exclude_codes=exclude_codes,
        allow_unidentified=allow_unidentified,
    )
    working_palette = reduce_palette_for_image(
        rgb,
        active,
        base_palette,
        max_colors=max_colors,
        color_space=color_space,
        random_state=random_state,
    )
    result = quantize_image(rgb, active, working_palette, method=quantize, color_space=color_space)

    return Pattern(
        width=width,
        height=height,
        palette=working_palette,
        indices=result.indices,
        rgb_image=result.rgb_image,
        active_mask=result.active_mask,
        error=result.error,
        metadata={
            "fit": fit,
            "background": background,
            "alpha_threshold": alpha_threshold,
            "resample": resample,
            "color_space": color_space,
            "quantize": quantize,
            "max_colors": max_colors,
        },
    )


def generate_pattern_with_options(image: Union[str, Path, Image.Image], options: PatternOptions) -> Pattern:
    """
    Generate a pattern from a :class:`PatternOptions` object.
    """

    return generate_pattern(
        image,
        width=options.width,
        height=options.height,
        palette=options.palette,
        fit=options.fit,
        background=options.background,
        alpha_threshold=options.alpha_threshold,
        resample=options.resample,
        color_space=options.color_space,
        quantize=options.quantize,
        max_colors=options.max_colors,
        include_codes=options.include_codes,
        exclude_codes=options.exclude_codes,
        allow_unidentified=options.allow_unidentified,
        random_state=options.random_state,
    )
