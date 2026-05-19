"""
Image loading and preprocessing helpers.

This module keeps image preparation independent from palette quantization.  The
high-level :func:`pypindou.pattern.generate_pattern` API uses these helpers to
load user images, remove transparent background noise, resize to a bead grid,
and optionally apply lightweight photographic adjustments before color
matching.

Example::

    >>> from PIL import Image
    >>> from pypindou.image.preprocess import enhance_image, resize_image
    >>> image = Image.new("RGBA", (16, 16), (200, 120, 80, 255))
    >>> resize_image(enhance_image(image, contrast=1.1), (8, 8)).size
    (8, 8)
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Tuple, Union

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

FitMode = Literal["contain", "cover", "stretch"]
BackgroundMode = Literal["keep", "white", "transparent"]
ResampleMode = Literal["nearest", "box", "bilinear", "bicubic", "lanczos"]
PreprocessMode = Literal["none", "smooth", "median", "edge"]


_RESAMPLE = {
    "nearest": Image.Resampling.NEAREST,
    "box": Image.Resampling.BOX,
    "bilinear": Image.Resampling.BILINEAR,
    "bicubic": Image.Resampling.BICUBIC,
    "lanczos": Image.Resampling.LANCZOS,
}


def load_image(image: Union[str, Path, Image.Image]) -> Image.Image:
    """
    Load an image as RGBA.

    :param image: Source image, image path, or :class:`PIL.Image.Image`.
    :type image: Union[str, pathlib.Path, PIL.Image.Image]
    :return: Loaded image converted to RGBA mode.
    :rtype: PIL.Image.Image
    :raises FileNotFoundError: If ``image`` is a path and does not exist.

    Example::

        >>> from PIL import Image
        >>> load_image(Image.new("RGB", (1, 1))).mode
        'RGBA'
    """

    if isinstance(image, Image.Image):
        return image.convert("RGBA")
    return Image.open(image).convert("RGBA")


def resize_image(
    image: Image.Image,
    size: Tuple[int, int],
    *,
    fit: FitMode = "contain",
    background: Tuple[int, int, int, int] = (255, 255, 255, 0),
    resample: ResampleMode = "lanczos",
) -> Image.Image:
    """
    Resize an image to a bead-grid size.

    ``contain`` preserves the full image and pads the remaining grid with
    ``background``. ``cover`` fills the grid and crops overflow from the
    center. ``stretch`` ignores the source aspect ratio.

    :param image: Source image.
    :type image: PIL.Image.Image
    :param size: Target size as ``(width, height)``.
    :type size: Tuple[int, int]
    :param fit: Aspect-ratio strategy, defaults to ``"contain"``.
    :type fit: FitMode, optional
    :param background: RGBA background used by ``contain``, defaults to
        ``(255, 255, 255, 0)``.
    :type background: Tuple[int, int, int, int], optional
    :param resample: Pillow resampling strategy, defaults to ``"lanczos"``.
    :type resample: ResampleMode, optional
    :return: Resized RGBA image.
    :rtype: PIL.Image.Image
    :raises ValueError: If ``size`` is not positive or ``fit``/``resample`` is
        unsupported.

    Example::

        >>> from PIL import Image
        >>> resize_image(Image.new("RGBA", (10, 20)), (5, 5)).size
        (5, 5)
    """

    width, height = size
    if width <= 0 or height <= 0:
        raise ValueError("Target size should be positive.")
    if resample not in _RESAMPLE:
        raise ValueError(f"Unsupported resample mode: {resample!r}.")

    src = image.convert("RGBA")
    if fit == "stretch":
        return src.resize((width, height), _RESAMPLE[resample])

    sx = width / src.width
    sy = height / src.height
    if fit == "contain":
        scale = min(sx, sy)
    elif fit == "cover":
        scale = max(sx, sy)
    else:
        raise ValueError(f"Unsupported fit mode: {fit!r}.")
    resized = src.resize(
        (max(1, int(round(src.width * scale))), max(1, int(round(src.height * scale)))),
        _RESAMPLE[resample],
    )

    if fit == "cover":
        left = max(0, (resized.width - width) // 2)
        top = max(0, (resized.height - height) // 2)
        return resized.crop((left, top, left + width, top + height))

    canvas = Image.new("RGBA", (width, height), background)
    left = (width - resized.width) // 2
    top = (height - resized.height) // 2
    canvas.alpha_composite(resized, (left, top))
    return canvas


def enhance_image(
    image: Image.Image,
    *,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sharpness: float = 1.0,
    grayscale: float = 0.0,
) -> Image.Image:
    """
    Apply lightweight photographic adjustments while preserving alpha.

    Adjustment factors follow Pillow's :mod:`PIL.ImageEnhance` convention:
    ``1.0`` leaves the channel unchanged, values below ``1.0`` reduce the
    effect, and values above ``1.0`` increase it. ``grayscale`` is a blend
    ratio from the adjusted RGB image to its grayscale version.

    :param image: Source image.
    :type image: PIL.Image.Image
    :param brightness: Brightness factor, defaults to ``1.0``.
    :type brightness: float, optional
    :param contrast: Contrast factor, defaults to ``1.0``.
    :type contrast: float, optional
    :param saturation: Color saturation factor, defaults to ``1.0``.
    :type saturation: float, optional
    :param sharpness: Sharpness factor, defaults to ``1.0``.
    :type sharpness: float, optional
    :param grayscale: Grayscale blend ratio in ``[0.0, 1.0]``, defaults to
        ``0.0``.
    :type grayscale: float, optional
    :return: Adjusted RGBA image.
    :rtype: PIL.Image.Image
    :raises ValueError: If a factor is negative or ``grayscale`` is outside
        ``[0.0, 1.0]``.

    Example::

        >>> from PIL import Image
        >>> enhance_image(Image.new("RGBA", (2, 2)), contrast=1.2).mode
        'RGBA'
    """

    for name, value in {
        "brightness": brightness,
        "contrast": contrast,
        "saturation": saturation,
        "sharpness": sharpness,
    }.items():
        if value < 0:
            raise ValueError(f"{name} should be non-negative.")
    if not 0.0 <= grayscale <= 1.0:
        raise ValueError("grayscale should be in [0.0, 1.0].")

    src = image.convert("RGBA")
    alpha = src.getchannel("A")
    rgb = src.convert("RGB")
    if brightness != 1.0:
        rgb = ImageEnhance.Brightness(rgb).enhance(brightness)
    if contrast != 1.0:
        rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    if saturation != 1.0:
        rgb = ImageEnhance.Color(rgb).enhance(saturation)
    if sharpness != 1.0:
        rgb = ImageEnhance.Sharpness(rgb).enhance(sharpness)
    if grayscale:
        gray = ImageOps.grayscale(rgb).convert("RGB")
        rgb = Image.blend(rgb, gray, grayscale)

    result = rgb.convert("RGBA")
    result.putalpha(alpha)
    return result


def prefilter_image(
    image: Image.Image,
    *,
    mode: PreprocessMode = "none",
    radius: float = 1.0,
) -> Image.Image:
    """
    Denoise or sharpen an image before it is resized to the bead grid.

    ``smooth`` applies a mild Gaussian blur, ``median`` removes isolated
    sensor/compression speckles, and ``edge`` combines median filtering with
    a light unsharp mask.  The alpha channel is preserved unchanged.

    :param image: Source image.
    :type image: PIL.Image.Image
    :param mode: Pre-filtering strategy, defaults to ``"none"``.
    :type mode: PreprocessMode, optional
    :param radius: Filter radius or median radius, defaults to ``1.0``.
    :type radius: float, optional
    :return: Filtered RGBA image.
    :rtype: PIL.Image.Image
    :raises ValueError: If ``radius`` is negative or ``mode`` is unsupported.

    Example::

        >>> from PIL import Image
        >>> prefilter_image(Image.new("RGBA", (4, 4)), mode="median").size
        (4, 4)
    """

    if radius < 0:
        raise ValueError("radius should be non-negative.")

    src = image.convert("RGBA")
    if mode == "none" or radius == 0:
        return src

    alpha = src.getchannel("A")
    rgb = src.convert("RGB")
    if mode == "smooth":
        filtered = rgb.filter(ImageFilter.GaussianBlur(radius=radius))
    elif mode == "median":
        size = max(3, int(round(radius)) * 2 + 1)
        if size % 2 == 0:
            size += 1
        filtered = rgb.filter(ImageFilter.MedianFilter(size=size))
    elif mode == "edge":
        filtered = rgb.filter(ImageFilter.MedianFilter(size=3))
        filtered = filtered.filter(ImageFilter.UnsharpMask(radius=max(1.0, radius), percent=90, threshold=4))
    else:
        raise ValueError(f"Unsupported prefilter mode: {mode!r}.")

    result = filtered.convert("RGBA")
    result.putalpha(alpha)
    return result


def remove_background_by_alpha(image: Image.Image, *, alpha_threshold: int = 16) -> Image.Image:
    """
    Set low-alpha pixels to fully transparent.

    :param image: Source image.
    :type image: PIL.Image.Image
    :param alpha_threshold: Pixels with alpha at or below this value become
        fully transparent, defaults to ``16``.
    :type alpha_threshold: int, optional
    :return: RGBA image with low-alpha pixels cleared.
    :rtype: PIL.Image.Image
    :raises ValueError: If ``alpha_threshold`` is outside ``[0, 255]``.

    Example::

        >>> from PIL import Image
        >>> img = Image.new("RGBA", (1, 1), (1, 2, 3, 0))
        >>> remove_background_by_alpha(img).getpixel((0, 0))
        (0, 0, 0, 0)
    """

    if not 0 <= alpha_threshold <= 255:
        raise ValueError("alpha_threshold should be in [0, 255].")

    arr = np.asarray(image.convert("RGBA")).copy()
    mask = arr[:, :, 3] <= alpha_threshold
    arr[mask] = (0, 0, 0, 0)
    return Image.fromarray(arr, mode="RGBA")


def rgba_to_rgb_array(
    image: Image.Image,
    *,
    background: BackgroundMode = "white",
    alpha_threshold: int = 16,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert an RGBA image to an RGB array and an active-pixel mask.

    :param image: Source image.
    :type image: PIL.Image.Image
    :param background: Alpha handling strategy, defaults to ``"white"``.
    :type background: BackgroundMode, optional
    :param alpha_threshold: Alpha threshold used by transparent mode, defaults
        to ``16``.
    :type alpha_threshold: int, optional
    :return: RGB ``uint8`` array and boolean active-pixel mask.
    :rtype: Tuple[numpy.ndarray, numpy.ndarray]
    :raises ValueError: If ``background`` is unsupported.

    Example::

        >>> from PIL import Image
        >>> rgb, active = rgba_to_rgb_array(Image.new("RGBA", (1, 1)))
        >>> rgb.shape, active.shape
        ((1, 1, 3), (1, 1))
    """

    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    alpha = rgba[:, :, 3]
    active = alpha > alpha_threshold

    if background == "transparent":
        rgb = rgba[:, :, :3].copy()
    elif background == "white":
        rgb = rgba[:, :, :3].astype(np.float64)
        alpha_f = (alpha.astype(np.float64) / 255.0)[:, :, None]
        rgb = rgb * alpha_f + 255.0 * (1.0 - alpha_f)
        rgb = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)
        active = np.ones(alpha.shape, dtype=bool)
    elif background == "keep":
        rgb = rgba[:, :, :3].copy()
        active = np.ones(alpha.shape, dtype=bool)
    else:
        raise ValueError(f"Unsupported background mode: {background!r}.")

    return rgb, active
