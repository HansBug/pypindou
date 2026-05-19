"""
Image quantization against bead palettes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Tuple

import numpy as np
from sklearn.cluster import MiniBatchKMeans

from pypindou.color import ColorSpace, Palette, convert_colors

QuantizeMethod = Literal["nearest", "floyd-steinberg"]


@dataclass(frozen=True)
class QuantizationResult:
    """
    Result of mapping an image to palette indices.
    """

    indices: np.ndarray
    active_mask: np.ndarray
    rgb_image: np.ndarray
    error: np.ndarray


def _palette_arrays(palette: Palette, color_space: ColorSpace) -> Tuple[np.ndarray, np.ndarray]:
    rgb = np.asarray([color.rgb for color in palette.colors], dtype=np.float64)
    return rgb, convert_colors(rgb, color_space=color_space)


def nearest_indices(
    pixels: np.ndarray,
    palette: Palette,
    *,
    color_space: ColorSpace = "lab",
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Map ``(n, 3)`` RGB pixels to nearest palette indices.
    """

    source = np.asarray(pixels, dtype=np.float64).reshape((-1, 3))
    palette_rgb, palette_space = _palette_arrays(palette, color_space)
    source_space = convert_colors(source, color_space=color_space)

    distances = ((source_space[:, None, :] - palette_space[None, :, :]) ** 2).sum(axis=2)
    indices = distances.argmin(axis=1)
    mapped = palette_rgb[indices]
    error = np.sqrt(((source - mapped) ** 2).mean(axis=1))
    return indices.astype(np.int32), error


def reduce_palette_for_image(
    rgb: np.ndarray,
    active_mask: np.ndarray,
    palette: Palette,
    *,
    max_colors: Optional[int],
    color_space: ColorSpace = "lab",
    random_state: int = 0,
) -> Palette:
    """
    Choose a palette subset for one image.
    """

    if max_colors is None or max_colors >= palette.size:
        return palette
    if max_colors <= 0:
        raise ValueError("max_colors should be positive.")

    pixels = np.asarray(rgb, dtype=np.uint8)[active_mask]
    if len(pixels) == 0:
        return palette.filter(max_colors=max_colors)

    clusters = min(max_colors, len(pixels))
    if clusters == 1:
        centers = np.asarray([pixels.mean(axis=0)])
    else:
        model = MiniBatchKMeans(n_clusters=clusters, n_init=3, random_state=random_state, batch_size=2048)
        model.fit(convert_colors(pixels, color_space=color_space))
        if color_space == "lab":
            centers = pixels[
                np.argmin(
                    ((convert_colors(pixels, color_space=color_space)[:, None, :] - model.cluster_centers_[None, :, :]) ** 2).sum(
                        axis=2
                    ),
                    axis=0,
                )
            ]
        else:
            centers = model.cluster_centers_

    nearest, _ = nearest_indices(centers, palette, color_space=color_space)
    selected = []
    seen = set()
    for idx in nearest.tolist():
        if idx not in seen:
            selected.append(palette.colors[idx].code)
            seen.add(idx)

    if len(selected) < max_colors:
        full_indices, _ = nearest_indices(pixels, palette, color_space=color_space)
        counts = np.bincount(full_indices, minlength=palette.size)
        for idx in counts.argsort()[::-1].tolist():
            if idx not in seen:
                selected.append(palette.colors[idx].code)
                seen.add(idx)
            if len(selected) >= max_colors:
                break

    return palette.filter(include_codes=selected)


def _nearest_one(rgb: np.ndarray, palette_rgb: np.ndarray, palette_space: np.ndarray, color_space: ColorSpace) -> int:
    point = convert_colors(np.asarray(rgb, dtype=np.float64).reshape((1, 3)), color_space=color_space)[0]
    return int(((palette_space - point) ** 2).sum(axis=1).argmin())


def quantize_image(
    rgb: np.ndarray,
    active_mask: np.ndarray,
    palette: Palette,
    *,
    method: QuantizeMethod = "nearest",
    color_space: ColorSpace = "lab",
) -> QuantizationResult:
    """
    Quantize an RGB image to bead palette indices.
    """

    image = np.asarray(rgb, dtype=np.uint8)
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("rgb image should have shape (h, w, 3).")
    active = np.asarray(active_mask, dtype=bool)
    if active.shape != image.shape[:2]:
        raise ValueError("active_mask should match image height and width.")

    h, w = active.shape
    indices = np.full((h, w), -1, dtype=np.int32)
    error = np.zeros((h, w), dtype=np.float64)
    output = np.zeros((h, w, 3), dtype=np.uint8)
    palette_rgb, palette_space = _palette_arrays(palette, color_space)

    if method == "nearest":
        flat = image[active]
        if len(flat):
            mapped, err = nearest_indices(flat, palette, color_space=color_space)
            indices[active] = mapped
            output[active] = np.rint(palette_rgb[mapped]).astype(np.uint8)
            error[active] = err
        return QuantizationResult(indices=indices, active_mask=active, rgb_image=output, error=error)

    if method != "floyd-steinberg":
        raise ValueError(f"Unsupported quantize method: {method!r}.")

    work = image.astype(np.float64).copy()
    for y in range(h):
        for x in range(w):
            if not active[y, x]:
                continue
            old = np.clip(work[y, x], 0, 255)
            idx = _nearest_one(old, palette_rgb, palette_space, color_space)
            new = palette_rgb[idx]
            indices[y, x] = idx
            output[y, x] = np.rint(new).astype(np.uint8)
            error[y, x] = float(np.sqrt(((old - new) ** 2).mean()))
            diff = old - new
            for dx, dy, weight in ((1, 0, 7 / 16), (-1, 1, 3 / 16), (0, 1, 5 / 16), (1, 1, 1 / 16)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and active[ny, nx]:
                    work[ny, nx] += diff * weight

    return QuantizationResult(indices=indices, active_mask=active, rgb_image=output, error=error)
