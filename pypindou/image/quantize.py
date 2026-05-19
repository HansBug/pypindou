"""
Image quantization against bead palettes.

The quantizers in this module map RGB pixels to indices in a
:class:`pypindou.color.Palette`.  The high-level pattern generator uses the
same result structure for direct nearest-color matching and Floyd-Steinberg
dithering, then optionally runs post-processing that makes the final bead grid
more practical for manual assembly.

Example::

    >>> import numpy as np
    >>> from pypindou.color import BeadColor, Palette
    >>> from pypindou.image.quantize import quantize_image
    >>> palette = Palette("bw", "Black/White", (BeadColor("K", (0, 0, 0)), BeadColor("W", (255, 255, 255))))
    >>> result = quantize_image(np.array([[[250, 250, 250]]], dtype=np.uint8), np.ones((1, 1), dtype=bool), palette)
    >>> result.indices.tolist()
    [[1]]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Tuple

import numpy as np
from sklearn.cluster import MiniBatchKMeans

from pypindou.color import ColorSpace, Palette, convert_colors

QuantizeMethod = Literal["nearest", "floyd-steinberg"]
CleanupMode = Literal["none", "majority"]


@dataclass(frozen=True)
class QuantizationResult:
    """
    Result of mapping an image to palette indices.

    :param indices: Integer palette-index grid, using ``-1`` for inactive
        pixels.
    :type indices: numpy.ndarray
    :param active_mask: Boolean mask that marks beads included in the pattern.
    :type active_mask: numpy.ndarray
    :param rgb_image: Quantized RGB preview image.
    :type rgb_image: numpy.ndarray
    :param error: Per-pixel root mean square RGB error.
    :type error: numpy.ndarray
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

    :param pixels: RGB pixels with shape ``(n, 3)``.
    :type pixels: numpy.ndarray
    :param palette: Palette used for matching.
    :type palette: pypindou.color.Palette
    :param color_space: Distance space, defaults to ``"lab"``.
    :type color_space: pypindou.color.ColorSpace, optional
    :return: Palette indices and per-pixel RMS RGB error.
    :rtype: Tuple[numpy.ndarray, numpy.ndarray]

    Example::

        >>> import numpy as np
        >>> from pypindou.color import BeadColor, Palette
        >>> palette = Palette("p", "P", (BeadColor("R", (255, 0, 0)), BeadColor("B", (0, 0, 255))))
        >>> nearest_indices(np.array([[250, 0, 0]], dtype=np.uint8), palette, color_space="rgb")[0].tolist()
        [0]
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

    Dominant colors are estimated from active image pixels and then snapped to
    the nearest real bead colors.  The result is useful for human-friendly
    charts where the number of colors should be capped before final
    quantization.

    :param rgb: Source RGB image with shape ``(h, w, 3)``.
    :type rgb: numpy.ndarray
    :param active_mask: Boolean active-pixel mask with shape ``(h, w)``.
    :type active_mask: numpy.ndarray
    :param palette: Source palette.
    :type palette: pypindou.color.Palette
    :param max_colors: Maximum number of colors to keep. ``None`` keeps the
        original palette.
    :type max_colors: Optional[int]
    :param color_space: Distance space, defaults to ``"lab"``.
    :type color_space: pypindou.color.ColorSpace, optional
    :param random_state: Random seed for MiniBatchKMeans, defaults to ``0``.
    :type random_state: int, optional
    :return: Filtered palette.
    :rtype: pypindou.color.Palette
    :raises ValueError: If ``max_colors`` is not positive.
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


def _validate_inputs(rgb: np.ndarray, active_mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    image = np.asarray(rgb, dtype=np.uint8)
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("rgb image should have shape (h, w, 3).")
    active = np.asarray(active_mask, dtype=bool)
    if active.shape != image.shape[:2]:
        raise ValueError("active_mask should match image height and width.")
    return image, active


def _rebuild_result(indices: np.ndarray, active: np.ndarray, image: np.ndarray, palette_rgb: np.ndarray) -> QuantizationResult:
    h, w = active.shape
    output = np.zeros((h, w, 3), dtype=np.uint8)
    error = np.zeros((h, w), dtype=np.float64)
    valid = active & (indices >= 0)
    if np.any(valid):
        mapped = palette_rgb[indices[valid]]
        output[valid] = np.rint(mapped).astype(np.uint8)
        source = image.astype(np.float64)[valid]
        error[valid] = np.sqrt(((source - mapped) ** 2).mean(axis=1))
    return QuantizationResult(indices=indices.astype(np.int32), active_mask=active, rgb_image=output, error=error)


def cleanup_quantization(
    indices: np.ndarray,
    active_mask: np.ndarray,
    *,
    mode: CleanupMode = "majority",
    passes: int = 1,
    threshold: int = 5,
) -> np.ndarray:
    """
    Smooth isolated palette-index noise after quantization.

    The majority cleaner looks at the 8-neighborhood of every active pixel and
    replaces the current index when at least ``threshold`` neighbors agree on a
    different color.  It is intentionally conservative: inactive pixels and
    boundaries are preserved.

    :param indices: Palette-index grid, using ``-1`` for inactive pixels.
    :type indices: numpy.ndarray
    :param active_mask: Boolean active-pixel mask.
    :type active_mask: numpy.ndarray
    :param mode: Cleanup strategy, defaults to ``"majority"``.
    :type mode: CleanupMode, optional
    :param passes: Number of cleanup passes, defaults to ``1``.
    :type passes: int, optional
    :param threshold: Minimum equal-neighbor count needed to replace one
        pixel, defaults to ``5``.
    :type threshold: int, optional
    :return: Cleaned palette-index grid.
    :rtype: numpy.ndarray
    :raises ValueError: If arguments are outside supported ranges.

    Example::

        >>> import numpy as np
        >>> grid = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.int32)
        >>> cleanup_quantization(grid, np.ones((3, 3), dtype=bool), threshold=5).tolist()
        [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
    """

    if passes < 0:
        raise ValueError("passes should be non-negative.")
    if not 1 <= threshold <= 8:
        raise ValueError("threshold should be in [1, 8].")
    if mode not in ("none", "majority"):
        raise ValueError(f"Unsupported cleanup mode: {mode!r}.")
    if mode == "none" or passes == 0:
        return np.asarray(indices, dtype=np.int32).copy()

    current = np.asarray(indices, dtype=np.int32).copy()
    active = np.asarray(active_mask, dtype=bool)
    if current.shape != active.shape:
        raise ValueError("indices and active_mask should have the same shape.")

    h, w = current.shape
    for _ in range(passes):
        updated = current.copy()
        changed = False
        for y in range(h):
            for x in range(w):
                if not active[y, x] or current[y, x] < 0:
                    continue
                neighbors = []
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and active[ny, nx] and current[ny, nx] >= 0:
                            neighbors.append(int(current[ny, nx]))
                if not neighbors:
                    continue
                counts = np.bincount(np.asarray(neighbors, dtype=np.int32))
                best = int(counts.argmax())
                if best != int(current[y, x]) and int(counts[best]) >= threshold:
                    updated[y, x] = best
                    changed = True
        current = updated
        if not changed:
            break
    return current


def merge_small_regions(
    indices: np.ndarray,
    active_mask: np.ndarray,
    *,
    min_size: int = 0,
    connectivity: int = 4,
) -> np.ndarray:
    """
    Merge tiny connected components into neighboring colors.

    Components smaller than ``min_size`` are replaced with the most frequent
    neighboring palette index around the component.  This reduces single-bead
    islands without requiring any image-domain dependencies.

    :param indices: Palette-index grid, using ``-1`` for inactive pixels.
    :type indices: numpy.ndarray
    :param active_mask: Boolean active-pixel mask.
    :type active_mask: numpy.ndarray
    :param min_size: Minimum region size to preserve. ``0`` disables merging,
        defaults to ``0``.
    :type min_size: int, optional
    :param connectivity: Neighbor connectivity, either ``4`` or ``8``,
        defaults to ``4``.
    :type connectivity: int, optional
    :return: Region-cleaned palette-index grid.
    :rtype: numpy.ndarray
    :raises ValueError: If shapes or argument values are invalid.
    """

    if min_size <= 1:
        return np.asarray(indices, dtype=np.int32).copy()
    if connectivity not in (4, 8):
        raise ValueError("connectivity should be 4 or 8.")

    current = np.asarray(indices, dtype=np.int32).copy()
    active = np.asarray(active_mask, dtype=bool)
    if current.shape != active.shape:
        raise ValueError("indices and active_mask should have the same shape.")
    if min_size < 0:
        raise ValueError("min_size should be non-negative.")

    h, w = current.shape
    offsets4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    offsets8 = offsets4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
    offsets = offsets4 if connectivity == 4 else offsets8

    visited = np.zeros((h, w), dtype=bool)
    for y in range(h):
        for x in range(w):
            if visited[y, x] or not active[y, x] or current[y, x] < 0:
                continue

            color = int(current[y, x])
            stack = [(y, x)]
            visited[y, x] = True
            component = []
            neighbor_colors = []
            while stack:
                cy, cx = stack.pop()
                component.append((cy, cx))
                for dx, dy in offsets:
                    ny, nx = cy + dy, cx + dx
                    if not (0 <= ny < h and 0 <= nx < w) or not active[ny, nx] or current[ny, nx] < 0:
                        continue
                    other = int(current[ny, nx])
                    if other == color:
                        if not visited[ny, nx]:
                            visited[ny, nx] = True
                            stack.append((ny, nx))
                    else:
                        neighbor_colors.append(other)

            if len(component) >= min_size or not neighbor_colors:
                continue
            counts = np.bincount(np.asarray(neighbor_colors, dtype=np.int32))
            replacement = int(counts.argmax())
            for cy, cx in component:
                current[cy, cx] = replacement
    return current


def quantize_image(
    rgb: np.ndarray,
    active_mask: np.ndarray,
    palette: Palette,
    *,
    method: QuantizeMethod = "nearest",
    color_space: ColorSpace = "lab",
    dither_strength: float = 1.0,
    cleanup: CleanupMode = "none",
    cleanup_passes: int = 0,
    cleanup_threshold: int = 5,
    min_region_size: int = 0,
) -> QuantizationResult:
    """
    Quantize an RGB image to bead palette indices.

    ``nearest`` maps every active pixel independently. ``floyd-steinberg``
    diffuses quantization error to later pixels and accepts ``dither_strength``
    in ``[0.0, 1.0]``.  Cleanup runs after quantization and is intended to make
    human assembly easier.

    :param rgb: Source RGB image with shape ``(h, w, 3)``.
    :type rgb: numpy.ndarray
    :param active_mask: Boolean active-pixel mask.
    :type active_mask: numpy.ndarray
    :param palette: Palette used for matching.
    :type palette: pypindou.color.Palette
    :param method: Quantization method, defaults to ``"nearest"``.
    :type method: QuantizeMethod, optional
    :param color_space: Distance space, defaults to ``"lab"``.
    :type color_space: pypindou.color.ColorSpace, optional
    :param dither_strength: Floyd-Steinberg diffusion strength in ``[0.0,
        1.0]``, defaults to ``1.0``.
    :type dither_strength: float, optional
    :param cleanup: Post-quantization cleanup mode, defaults to ``"none"``.
    :type cleanup: CleanupMode, optional
    :param cleanup_passes: Number of cleanup passes, defaults to ``0``.
    :type cleanup_passes: int, optional
    :param cleanup_threshold: Majority threshold, defaults to ``5``.
    :type cleanup_threshold: int, optional
    :param min_region_size: Regions smaller than this value are merged into
        neighboring colors, defaults to ``0``.
    :type min_region_size: int, optional
    :return: Quantization result.
    :rtype: QuantizationResult
    :raises ValueError: If inputs or options are invalid.
    """

    if not 0.0 <= dither_strength <= 1.0:
        raise ValueError("dither_strength should be in [0.0, 1.0].")

    image, active = _validate_inputs(rgb, active_mask)
    h, w = active.shape
    indices = np.full((h, w), -1, dtype=np.int32)
    output = np.zeros((h, w, 3), dtype=np.uint8)
    error = np.zeros((h, w), dtype=np.float64)
    palette_rgb, palette_space = _palette_arrays(palette, color_space)

    if method == "nearest":
        flat = image[active]
        if len(flat):
            mapped, err = nearest_indices(flat, palette, color_space=color_space)
            indices[active] = mapped
            output[active] = np.rint(palette_rgb[mapped]).astype(np.uint8)
            error[active] = err
    elif method == "floyd-steinberg":
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
                diff = (old - new) * dither_strength
                for dx, dy, weight in ((1, 0, 7 / 16), (-1, 1, 3 / 16), (0, 1, 5 / 16), (1, 1, 1 / 16)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and active[ny, nx]:
                        work[ny, nx] += diff * weight
    else:
        raise ValueError(f"Unsupported quantize method: {method!r}.")

    if cleanup != "none" or cleanup_passes:
        indices = cleanup_quantization(
            indices,
            active,
            mode=cleanup,
            passes=cleanup_passes,
            threshold=cleanup_threshold,
        )
    if min_region_size:
        indices = merge_small_regions(indices, active, min_size=min_region_size)
    if cleanup != "none" or cleanup_passes or min_region_size:
        return _rebuild_result(indices, active, image, palette_rgb)
    return QuantizationResult(indices=indices, active_mask=active, rgb_image=output, error=error)
