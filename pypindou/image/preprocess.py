"""
Image loading and preprocessing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Tuple

import numpy as np
from PIL import Image

FitMode = Literal["contain", "cover", "stretch"]
BackgroundMode = Literal["keep", "white", "transparent"]
ResampleMode = Literal["nearest", "box", "bilinear", "bicubic", "lanczos"]


_RESAMPLE = {
    "nearest": Image.Resampling.NEAREST,
    "box": Image.Resampling.BOX,
    "bilinear": Image.Resampling.BILINEAR,
    "bicubic": Image.Resampling.BICUBIC,
    "lanczos": Image.Resampling.LANCZOS,
}


def load_image(image: str | Path | Image.Image) -> Image.Image:
    """
    Load an image as RGBA.
    """

    if isinstance(image, Image.Image):
        return image.convert("RGBA")
    return Image.open(image).convert("RGBA")


def resize_image(
    image: Image.Image,
    size: Tuple[int, int],
    *,
    fit: FitMode = "contain",
    background: tuple[int, int, int, int] = (255, 255, 255, 0),
    resample: ResampleMode = "lanczos",
) -> Image.Image:
    """
    Resize an image to a bead-grid size.
    """

    width, height = size
    if width <= 0 or height <= 0:
        raise ValueError("Target size should be positive.")

    src = image.convert("RGBA")
    if fit == "stretch":
        return src.resize((width, height), _RESAMPLE[resample])

    sx = width / src.width
    sy = height / src.height
    scale = min(sx, sy) if fit == "contain" else max(sx, sy)
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


def remove_background_by_alpha(image: Image.Image, *, alpha_threshold: int = 16) -> Image.Image:
    """
    Set low-alpha pixels to fully transparent.
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
) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert an RGBA image to an RGB array and an active-pixel mask.
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
