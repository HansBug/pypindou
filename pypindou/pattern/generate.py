"""
High-level image-to-pattern generation API.

The functions in this module connect image preprocessing, palette filtering,
color quantization, and :class:`pypindou.pattern.Pattern` construction.  They
are the main public entry point for applications that need a pure Python
image-to-bead-pattern workflow.

Example::

    >>> from PIL import Image
    >>> from pypindou.pattern import generate_pattern
    >>> image = Image.new("RGB", (4, 4), "white")
    >>> pattern = generate_pattern(image, width=4, height=4, max_colors=4, color_space="rgb")
    >>> pattern.board_size
    (4, 4)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Union

from PIL import Image

from pypindou.color import ColorSpace, Palette, get_palette
from pypindou.image import (
    BackgroundMode,
    CleanupMode,
    FitMode,
    PreprocessMode,
    QuantizeMethod,
    ResampleMode,
    enhance_image,
    load_image,
    prefilter_image,
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

    :param width: Target bead-grid width.
    :type width: int
    :param height: Target bead-grid height.
    :type height: int
    :param palette: Built-in palette id or explicit palette object, defaults to
        ``"mard-221-alfonse-doudou"``.
    :type palette: Union[str, pypindou.color.Palette], optional
    :param fit: Image fit strategy, defaults to ``"contain"``.
    :type fit: pypindou.image.FitMode, optional
    :param background: Alpha handling strategy, defaults to ``"white"``.
    :type background: pypindou.image.BackgroundMode, optional
    :param alpha_threshold: Transparent-pixel threshold, defaults to ``16``.
    :type alpha_threshold: int, optional
    :param resample: Resize filter, defaults to ``"lanczos"``.
    :type resample: pypindou.image.ResampleMode, optional
    :param prefilter: Optional pre-resize denoising or edge-preserving filter,
        defaults to ``"none"``.
    :type prefilter: pypindou.image.PreprocessMode, optional
    :param prefilter_radius: Radius used by the prefilter, defaults to ``1.0``.
    :type prefilter_radius: float, optional
    :param brightness: Brightness adjustment factor, defaults to ``1.0``.
    :type brightness: float, optional
    :param contrast: Contrast adjustment factor, defaults to ``1.0``.
    :type contrast: float, optional
    :param saturation: Saturation adjustment factor, defaults to ``1.0``.
    :type saturation: float, optional
    :param sharpness: Sharpness adjustment factor, defaults to ``1.0``.
    :type sharpness: float, optional
    :param grayscale: Grayscale blend ratio, defaults to ``0.0``.
    :type grayscale: float, optional
    :param color_space: Color distance space, defaults to ``"lab"``.
    :type color_space: pypindou.color.ColorSpace, optional
    :param quantize: Quantization method, defaults to ``"nearest"``.
    :type quantize: pypindou.image.QuantizeMethod, optional
    :param dither_strength: Floyd-Steinberg diffusion strength, defaults to
        ``1.0``.
    :type dither_strength: float, optional
    :param max_colors: Maximum number of bead colors to use, defaults to
        ``None``.
    :type max_colors: Optional[int], optional
    :param cleanup: Post-quantization cleanup mode, defaults to ``"none"``.
    :type cleanup: pypindou.image.CleanupMode, optional
    :param cleanup_passes: Number of cleanup passes, defaults to ``0``.
    :type cleanup_passes: int, optional
    :param cleanup_threshold: Majority threshold for cleanup, defaults to
        ``5``.
    :type cleanup_threshold: int, optional
    :param min_region_size: Small connected regions below this size are merged,
        defaults to ``0``.
    :type min_region_size: int, optional
    :param include_codes: Optional allowed color-code list.
    :type include_codes: Optional[Tuple[str, ...]], optional
    :param exclude_codes: Optional excluded color-code list.
    :type exclude_codes: Optional[Tuple[str, ...]], optional
    :param allow_unidentified: Whether to keep colors marked unidentified,
        defaults to ``False``.
    :type allow_unidentified: bool, optional
    :param random_state: Random seed for palette reduction, defaults to ``0``.
    :type random_state: int, optional
    """

    width: int
    height: int
    palette: Union[str, Palette] = "mard-221-alfonse-doudou"
    fit: FitMode = "contain"
    background: BackgroundMode = "white"
    alpha_threshold: int = 16
    resample: ResampleMode = "lanczos"
    prefilter: PreprocessMode = "none"
    prefilter_radius: float = 1.0
    brightness: float = 1.0
    contrast: float = 1.0
    saturation: float = 1.0
    sharpness: float = 1.0
    grayscale: float = 0.0
    color_space: ColorSpace = "lab"
    quantize: QuantizeMethod = "nearest"
    dither_strength: float = 1.0
    max_colors: Optional[int] = None
    cleanup: CleanupMode = "none"
    cleanup_passes: int = 0
    cleanup_threshold: int = 5
    min_region_size: int = 0
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
    prefilter: PreprocessMode = "none",
    prefilter_radius: float = 1.0,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sharpness: float = 1.0,
    grayscale: float = 0.0,
    color_space: ColorSpace = "lab",
    quantize: QuantizeMethod = "nearest",
    dither_strength: float = 1.0,
    max_colors: Optional[int] = None,
    cleanup: CleanupMode = "none",
    cleanup_passes: int = 0,
    cleanup_threshold: int = 5,
    min_region_size: int = 0,
    include_codes: Optional[Tuple[str, ...]] = None,
    exclude_codes: Optional[Tuple[str, ...]] = None,
    allow_unidentified: bool = False,
    random_state: int = 0,
) -> Pattern:
    """
    Generate a fuse-bead pattern from an input image.

    The default path favors clean, editable regions over photographic texture:
    use ``max_colors`` to limit the palette, ``prefilter`` and enhancement
    options to simplify the source image, then optionally run ``cleanup`` and
    ``min_region_size`` to remove tiny color islands.  Enable
    ``quantize="floyd-steinberg"`` when visible dithering is preferred.

    :param image: Source image, image path, or :class:`PIL.Image.Image`.
    :type image: Union[str, pathlib.Path, PIL.Image.Image]
    :param width: Target bead-grid width.
    :type width: int
    :param height: Target bead-grid height.
    :type height: int
    :param palette: Built-in palette id or explicit palette object, defaults to
        ``"mard-221-alfonse-doudou"``.
    :type palette: Union[str, pypindou.color.Palette], optional
    :param fit: Image fit strategy, defaults to ``"contain"``.
    :type fit: pypindou.image.FitMode, optional
    :param background: Alpha handling strategy, defaults to ``"white"``.
    :type background: pypindou.image.BackgroundMode, optional
    :param alpha_threshold: Transparent-pixel threshold, defaults to ``16``.
    :type alpha_threshold: int, optional
    :param resample: Resize filter, defaults to ``"lanczos"``.
    :type resample: pypindou.image.ResampleMode, optional
    :param prefilter: Optional pre-resize filter, defaults to ``"none"``.
    :type prefilter: pypindou.image.PreprocessMode, optional
    :param prefilter_radius: Radius used by the prefilter, defaults to ``1.0``.
    :type prefilter_radius: float, optional
    :param brightness: Brightness adjustment factor, defaults to ``1.0``.
    :type brightness: float, optional
    :param contrast: Contrast adjustment factor, defaults to ``1.0``.
    :type contrast: float, optional
    :param saturation: Saturation adjustment factor, defaults to ``1.0``.
    :type saturation: float, optional
    :param sharpness: Sharpness adjustment factor, defaults to ``1.0``.
    :type sharpness: float, optional
    :param grayscale: Grayscale blend ratio, defaults to ``0.0``.
    :type grayscale: float, optional
    :param color_space: Color distance space, defaults to ``"lab"``.
    :type color_space: pypindou.color.ColorSpace, optional
    :param quantize: Quantization method, defaults to ``"nearest"``.
    :type quantize: pypindou.image.QuantizeMethod, optional
    :param dither_strength: Floyd-Steinberg diffusion strength, defaults to
        ``1.0``.
    :type dither_strength: float, optional
    :param max_colors: Maximum number of bead colors to use, defaults to
        ``None``.
    :type max_colors: Optional[int], optional
    :param cleanup: Post-quantization cleanup mode, defaults to ``"none"``.
    :type cleanup: pypindou.image.CleanupMode, optional
    :param cleanup_passes: Number of cleanup passes, defaults to ``0``.
    :type cleanup_passes: int, optional
    :param cleanup_threshold: Majority threshold for cleanup, defaults to
        ``5``.
    :type cleanup_threshold: int, optional
    :param min_region_size: Regions smaller than this value are merged into
        neighboring colors, defaults to ``0``.
    :type min_region_size: int, optional
    :param include_codes: Optional allowed color-code list.
    :type include_codes: Optional[Tuple[str, ...]], optional
    :param exclude_codes: Optional excluded color-code list.
    :type exclude_codes: Optional[Tuple[str, ...]], optional
    :param allow_unidentified: Whether to keep colors marked unidentified,
        defaults to ``False``.
    :type allow_unidentified: bool, optional
    :param random_state: Random seed for palette reduction, defaults to ``0``.
    :type random_state: int, optional
    :return: Generated bead pattern.
    :rtype: pypindou.pattern.Pattern
    """

    src = load_image(image)
    src = remove_background_by_alpha(src, alpha_threshold=alpha_threshold)
    src = enhance_image(
        src,
        brightness=brightness,
        contrast=contrast,
        saturation=saturation,
        sharpness=sharpness,
        grayscale=grayscale,
    )
    src = prefilter_image(src, mode=prefilter, radius=prefilter_radius)
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
    result = quantize_image(
        rgb,
        active,
        working_palette,
        method=quantize,
        color_space=color_space,
        dither_strength=dither_strength,
        cleanup=cleanup,
        cleanup_passes=cleanup_passes,
        cleanup_threshold=cleanup_threshold,
        min_region_size=min_region_size,
    )

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
            "prefilter": prefilter,
            "prefilter_radius": prefilter_radius,
            "brightness": brightness,
            "contrast": contrast,
            "saturation": saturation,
            "sharpness": sharpness,
            "grayscale": grayscale,
            "color_space": color_space,
            "quantize": quantize,
            "dither_strength": dither_strength,
            "max_colors": max_colors,
            "cleanup": cleanup,
            "cleanup_passes": cleanup_passes,
            "cleanup_threshold": cleanup_threshold,
            "min_region_size": min_region_size,
        },
    )


def generate_pattern_with_options(image: Union[str, Path, Image.Image], options: PatternOptions) -> Pattern:
    """
    Generate a pattern from a :class:`PatternOptions` object.

    :param image: Source image, image path, or :class:`PIL.Image.Image`.
    :type image: Union[str, pathlib.Path, PIL.Image.Image]
    :param options: Pattern-generation options.
    :type options: PatternOptions
    :return: Generated bead pattern.
    :rtype: pypindou.pattern.Pattern
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
        prefilter=options.prefilter,
        prefilter_radius=options.prefilter_radius,
        brightness=options.brightness,
        contrast=options.contrast,
        saturation=options.saturation,
        sharpness=options.sharpness,
        grayscale=options.grayscale,
        color_space=options.color_space,
        quantize=options.quantize,
        dither_strength=options.dither_strength,
        max_colors=options.max_colors,
        cleanup=options.cleanup,
        cleanup_passes=options.cleanup_passes,
        cleanup_threshold=options.cleanup_threshold,
        min_region_size=options.min_region_size,
        include_codes=options.include_codes,
        exclude_codes=options.exclude_codes,
        allow_unidentified=options.allow_unidentified,
        random_state=options.random_state,
    )
