"""
Pattern data model and render helpers.

The :class:`Pattern` dataclass is the main structured output of
:func:`pypindou.pattern.generate_pattern`.  It stores the palette-index grid,
active bead mask, rendered RGB preview data, per-pixel error, and metadata that
describes how the pattern was generated.

Example::

    >>> import numpy as np
    >>> from pypindou.color import BeadColor, Palette
    >>> from pypindou.pattern.model import Pattern
    >>> palette = Palette("demo", "Demo", (BeadColor("001", (255, 255, 255)),))
    >>> pattern = Pattern(1, 1, palette, np.array([[0]]), np.array([[[255, 255, 255]]], dtype=np.uint8), np.ones((1, 1), dtype=bool), np.zeros((1, 1)))
    >>> pattern.bead_count
    1
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Literal, Mapping, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from pypindou.color import BeadColor, Palette

SymbolFormat = Literal["png", "svg"]
SymbolLabelMode = Literal["code", "short", "symbol"]

_GRID_RGB = (80, 80, 80)
_SVG_GRID = "#505050"
_SVG_FONT_FAMILY = "DejaVu Sans Mono, Consolas, Menlo, monospace"
_LABEL_MODES = ("code", "short", "symbol")


def _cell_padding(cell_size: int) -> int:
    return min(max(1, int(round(cell_size * 0.1))), max(0, cell_size // 3))


def _cell_inner_size(cell_size: int) -> Tuple[int, int, int]:
    padding = _cell_padding(cell_size)
    inner = max(1, cell_size - 2 * padding)
    return padding, inner, inner


def _load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=max(1, int(size)))
    except TypeError:
        return ImageFont.load_default()


def _text_bbox(font: ImageFont.ImageFont, label: str) -> Tuple[int, int, int, int]:
    bbox = font.getbbox(label)
    return int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])


def _label_for_color(color: BeadColor, mode: SymbolLabelMode) -> str:
    if mode == "code":
        return color.code
    if mode == "short":
        return color.code[-3:]
    if mode == "symbol":
        symbol = color.metadata.get("symbol")
        return str(symbol) if symbol else color.code[-3:]
    raise ValueError(f"Unsupported label mode: {mode!r}.")


def _check_label_mode(mode: str) -> SymbolLabelMode:
    if mode not in _LABEL_MODES:
        raise ValueError(f"Unsupported label mode: {mode!r}.")
    return mode  # type: ignore[return-value]


def _text_rgb_for_background(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
    luminance = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    return (0, 0, 0) if luminance > 150 else (255, 255, 255)


def _render_fitted_text(label: str, color: Tuple[int, int, int], inner_width: int, inner_height: int) -> Image.Image:
    font_size = max(1, inner_height)
    while font_size > 1:
        font = _load_font(font_size)
        left, top, right, bottom = _text_bbox(font, label)
        if bottom - top <= inner_height:
            break
        font_size -= 1
    font = _load_font(font_size)
    left, top, right, bottom = _text_bbox(font, label)
    width = max(1, right - left)
    height = max(1, bottom - top)

    text = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(text)
    draw.text((-left, -top), label, fill=(*color, 255), font=font)

    scale = min(1.0, inner_width / width, inner_height / height)
    if scale < 1.0:
        target = (max(1, int(width * scale)), max(1, int(height * scale)))
        text = text.resize(target, Image.Resampling.LANCZOS)
    return text


def _svg_text_plan(label: str, inner_width: int, inner_height: int) -> Tuple[float, float]:
    font_size = min(inner_height * 0.78, inner_width / max(1.0, len(label) * 0.62))
    font_size = max(1.0, font_size)
    text_length = min(inner_width, max(font_size * 0.35, len(label) * font_size * 0.62))
    return font_size, text_length


def _rgb_to_svg(rgb: Tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


@dataclass(frozen=True)
class Pattern:
    """
    A bead pattern generated from one image.

    :param width: Pattern width in beads.
    :type width: int
    :param height: Pattern height in beads.
    :type height: int
    :param palette: Palette used by ``indices``.
    :type palette: pypindou.color.Palette
    :param indices: Palette-index grid with shape ``(height, width)``.
    :type indices: numpy.ndarray
    :param rgb_image: Quantized RGB preview array with shape
        ``(height, width, 3)``.
    :type rgb_image: numpy.ndarray
    :param active_mask: Boolean mask of active beads.
    :type active_mask: numpy.ndarray
    :param error: Per-pixel quantization error.
    :type error: numpy.ndarray
    :param metadata: Generation metadata, defaults to an empty mapping.
    :type metadata: Mapping[str, Any], optional
    :raises ValueError: If array shapes do not match ``width`` and ``height``.
    """

    width: int
    height: int
    palette: Palette
    indices: np.ndarray
    rgb_image: np.ndarray
    active_mask: np.ndarray
    error: np.ndarray
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        indices = np.asarray(self.indices, dtype=np.int32)
        active = np.asarray(self.active_mask, dtype=bool)
        rgb = np.asarray(self.rgb_image, dtype=np.uint8)
        error = np.asarray(self.error, dtype=np.float64)

        if indices.shape != (self.height, self.width):
            raise ValueError("indices shape does not match pattern size.")
        if active.shape != (self.height, self.width):
            raise ValueError("active_mask shape does not match pattern size.")
        if error.shape != (self.height, self.width):
            raise ValueError("error shape does not match pattern size.")
        if rgb.shape != (self.height, self.width, 3):
            raise ValueError("rgb_image shape does not match pattern size.")

        object.__setattr__(self, "indices", indices)
        object.__setattr__(self, "active_mask", active)
        object.__setattr__(self, "rgb_image", rgb)
        object.__setattr__(self, "error", error)

    @property
    def bead_count(self) -> int:
        """
        Number of active beads.

        :return: Number of active beads.
        :rtype: int
        """

        return int(self.active_mask.sum())

    @property
    def board_size(self) -> Tuple[int, int]:
        """
        Pattern grid size as ``(width, height)``.

        :return: Pattern size.
        :rtype: Tuple[int, int]
        """

        return self.width, self.height

    def color_counts(self) -> Dict[str, int]:
        """
        Count beads by color code.

        :return: Mapping from bead color code to usage count.
        :rtype: Dict[str, int]
        """

        values = self.indices[self.active_mask]
        counts = Counter(int(item) for item in values if int(item) >= 0)
        return {
            self.palette.colors[idx].code: int(count)
            for idx, count in sorted(counts.items(), key=lambda item: self.palette.colors[item[0]].code)
        }

    def legend(self) -> List[Dict[str, Any]]:
        """
        Return legend rows sorted by count descending.

        :return: Legend rows with code, name, RGB, hex, count, and
            unidentified flag.
        :rtype: List[Dict[str, Any]]
        """

        counts = self.color_counts()
        rows = []
        for color in self.palette.colors:
            count = counts.get(color.code, 0)
            if count:
                rows.append(
                    {
                        "code": color.code,
                        "name": color.name,
                        "rgb": list(color.rgb),
                        "hex": color.hex,
                        "count": count,
                        "unidentified": color.unidentified,
                    }
                )
        return sorted(rows, key=lambda item: (-item["count"], item["code"]))

    def color_grid(self) -> List[List[Optional[str]]]:
        """
        Return the pattern grid as color codes.

        :return: Two-dimensional grid of color codes, using ``None`` for
            inactive cells.
        :rtype: List[List[Optional[str]]]
        """

        grid: List[List[Optional[str]]] = []
        for y in range(self.height):
            row: List[Optional[str]] = []
            for x in range(self.width):
                idx = int(self.indices[y, x])
                row.append(self.palette.colors[idx].code if idx >= 0 and self.active_mask[y, x] else None)
            grid.append(row)
        return grid

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the pattern to a JSON-serializable dictionary.

        :return: Dictionary representation of the pattern.
        :rtype: Dict[str, Any]
        """

        return {
            "width": self.width,
            "height": self.height,
            "bead_count": self.bead_count,
            "palette": {
                "id": self.palette.id,
                "title": self.palette.title,
            },
            "legend": self.legend(),
            "grid": self.color_grid(),
            "mean_error": float(self.error[self.active_mask].mean()) if self.bead_count else 0.0,
            "metadata": dict(self.metadata),
        }

    def to_image(self, *, scale: int = 16, grid: bool = True) -> Image.Image:
        """
        Render the pattern as a preview image.

        :param scale: Pixel size of one bead cell, defaults to ``16``.
        :type scale: int, optional
        :param grid: Whether to draw cell grid lines, defaults to ``True``.
        :type grid: bool, optional
        :return: RGB preview image.
        :rtype: PIL.Image.Image
        :raises ValueError: If ``scale`` is not positive.
        """

        if scale <= 0:
            raise ValueError("scale should be positive.")

        canvas = Image.new("RGB", (self.width * scale, self.height * scale), "white")
        draw = ImageDraw.Draw(canvas)
        for y in range(self.height):
            for x in range(self.width):
                left, top = x * scale, y * scale
                box = (left, top, left + scale, top + scale)
                if self.active_mask[y, x] and self.indices[y, x] >= 0:
                    color = tuple(int(item) for item in self.rgb_image[y, x])
                    draw.rectangle(box, fill=color)
                else:
                    draw.rectangle(box, fill=(255, 255, 255))
                if grid and scale >= 4:
                    draw.rectangle(box, outline=(210, 210, 210))
        return canvas

    def to_symbol_image(
        self,
        *,
        cell_size: int = 24,
        show_grid: bool = True,
        label_mode: SymbolLabelMode = "code",
    ) -> Image.Image:
        """
        Render a PNG-compatible symbol map with bead-code labels.

        Labels are rendered into a transparent temporary image and scaled into
        the padded area of each cell.  This guarantees that even long color
        codes stay strictly inside their own cells in the returned bitmap.

        :param cell_size: Pixel size of one cell, defaults to ``24``.
        :type cell_size: int, optional
        :param show_grid: Whether to draw cell borders, defaults to ``True``.
        :type show_grid: bool, optional
        :param label_mode: Label text strategy, defaults to ``"code"``. Use
            ``"short"`` for the last three code characters or ``"symbol"``
            for upstream symbol metadata when available.
        :type label_mode: SymbolLabelMode, optional
        :return: RGB symbol image.
        :rtype: PIL.Image.Image
        :raises ValueError: If ``cell_size`` is not positive or
            ``label_mode`` is unsupported.
        """

        if cell_size <= 0:
            raise ValueError("cell_size should be positive.")
        label_mode = _check_label_mode(label_mode)

        canvas = Image.new("RGB", (self.width * cell_size, self.height * cell_size), "white")
        draw = ImageDraw.Draw(canvas)
        padding, inner_width, inner_height = _cell_inner_size(cell_size)
        for y in range(self.height):
            for x in range(self.width):
                left, top = x * cell_size, y * cell_size
                box = (left, top, left + cell_size, top + cell_size)
                if self.active_mask[y, x] and self.indices[y, x] >= 0:
                    color = self.palette.colors[int(self.indices[y, x])]
                    draw.rectangle(box, fill=color.rgb)
                    label = _label_for_color(color, label_mode)
                    if label:
                        text = _render_fitted_text(label, _text_rgb_for_background(color.rgb), inner_width, inner_height)
                        tx = left + padding + (inner_width - text.width) // 2
                        ty = top + padding + (inner_height - text.height) // 2
                        canvas.paste(text.convert("RGB"), (tx, ty), text)
                if show_grid:
                    draw.rectangle(box, outline=_GRID_RGB)
        return canvas

    def to_symbol_svg(
        self,
        *,
        cell_size: int = 24,
        show_grid: bool = True,
        label_mode: SymbolLabelMode = "code",
        font_family: str = _SVG_FONT_FAMILY,
    ) -> str:
        """
        Render a symbol map as SVG text.

        The SVG renderer uses the same cell padding and label strategy as
        :meth:`to_symbol_image`.  Each label is placed in a per-cell clip path
        and receives a conservative ``textLength`` constraint, so SVG viewers
        cannot draw code text outside its own cell.

        :param cell_size: SVG user-unit size of one cell, defaults to ``24``.
        :type cell_size: int, optional
        :param show_grid: Whether to draw cell borders, defaults to ``True``.
        :type show_grid: bool, optional
        :param label_mode: Label text strategy, defaults to ``"code"``.
        :type label_mode: SymbolLabelMode, optional
        :param font_family: SVG font-family declaration, defaults to a
            monospace fallback stack.
        :type font_family: str, optional
        :return: SVG document text.
        :rtype: str
        :raises ValueError: If ``cell_size`` is not positive or
            ``label_mode`` is unsupported.
        """

        if cell_size <= 0:
            raise ValueError("cell_size should be positive.")
        label_mode = _check_label_mode(label_mode)

        width = self.width * cell_size
        height = self.height * cell_size
        padding, inner_width, inner_height = _cell_inner_size(cell_size)
        font_family_text = escape(font_family, quote=True)

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges">'
            ),
            '  <rect width="100%" height="100%" fill="#FFFFFF"/>',
            "  <defs>",
        ]
        for y in range(self.height):
            for x in range(self.width):
                if self.active_mask[y, x] and self.indices[y, x] >= 0:
                    clip_id = f"cell-{x}-{y}-clip"
                    left = x * cell_size + padding
                    top = y * cell_size + padding
                    lines.append(
                        f'    <clipPath id="{clip_id}">'
                        f'<rect x="{left}" y="{top}" width="{inner_width}" height="{inner_height}"/>'
                        f"</clipPath>"
                    )
        lines.append("  </defs>")

        for y in range(self.height):
            for x in range(self.width):
                left, top = x * cell_size, y * cell_size
                stroke = f' stroke="{_SVG_GRID}" stroke-width="1"' if show_grid else ""
                if self.active_mask[y, x] and self.indices[y, x] >= 0:
                    color = self.palette.colors[int(self.indices[y, x])]
                    fill = _rgb_to_svg(color.rgb)
                    lines.append(
                        f'  <rect x="{left}" y="{top}" width="{cell_size}" height="{cell_size}" fill="{fill}"{stroke}/>'
                    )
                    label = _label_for_color(color, label_mode)
                    if label:
                        text_rgb = _text_rgb_for_background(color.rgb)
                        text_fill = _rgb_to_svg(text_rgb)
                        font_size, text_length = _svg_text_plan(label, inner_width, inner_height)
                        cx = left + cell_size / 2
                        cy = top + cell_size / 2
                        clip_id = f"cell-{x}-{y}-clip"
                        lines.append(
                            f'  <text x="{cx:.3f}" y="{cy:.3f}" fill="{text_fill}" '
                            f'font-family="{font_family_text}" font-size="{font_size:.3f}" '
                            f'text-anchor="middle" dominant-baseline="central" alignment-baseline="central" '
                            f'textLength="{text_length:.3f}" lengthAdjust="spacingAndGlyphs" '
                            f'clip-path="url(#{clip_id})">{escape(label)}</text>'
                        )
                else:
                    lines.append(
                        f'  <rect x="{left}" y="{top}" width="{cell_size}" height="{cell_size}" fill="#FFFFFF"{stroke}/>'
                    )
        lines.append("</svg>")
        return "\n".join(lines) + "\n"

    def save_symbol_chart(
        self,
        path: Union[str, Path],
        *,
        format: Optional[SymbolFormat] = None,
        cell_size: int = 24,
        show_grid: bool = True,
        label_mode: SymbolLabelMode = "code",
    ) -> Path:
        """
        Save a symbol chart as PNG or SVG.

        When ``format`` is omitted, it is inferred from the file suffix.  The
        PNG path uses :meth:`to_symbol_image`; the SVG path uses
        :meth:`to_symbol_svg`.

        :param path: Output path.
        :type path: Union[str, pathlib.Path]
        :param format: Output format, either ``"png"`` or ``"svg"``. When
            omitted, the suffix of ``path`` is used.
        :type format: Optional[SymbolFormat], optional
        :param cell_size: Size of one chart cell, defaults to ``24``.
        :type cell_size: int, optional
        :param show_grid: Whether to draw cell borders, defaults to ``True``.
        :type show_grid: bool, optional
        :param label_mode: Label text strategy, defaults to ``"code"``.
        :type label_mode: SymbolLabelMode, optional
        :return: Saved output path.
        :rtype: pathlib.Path
        :raises ValueError: If the format cannot be inferred or is unsupported.
        """

        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        fmt = (format or output.suffix.lstrip(".")).lower()
        if fmt == "png":
            self.to_symbol_image(cell_size=cell_size, show_grid=show_grid, label_mode=label_mode).save(output)
        elif fmt == "svg":
            output.write_text(
                self.to_symbol_svg(cell_size=cell_size, show_grid=show_grid, label_mode=label_mode),
                encoding="utf-8",
            )
        else:
            raise ValueError(f"Unsupported symbol chart format: {fmt!r}.")
        return output


def color_for_code(pattern: Pattern, code: str) -> BeadColor:
    """
    Return the palette color for ``code`` in a pattern.

    :param pattern: Pattern whose palette should be queried.
    :type pattern: Pattern
    :param code: Palette color code.
    :type code: str
    :return: Matching bead color.
    :rtype: pypindou.color.BeadColor
    :raises KeyError: If the code is not present in the pattern palette.
    """

    return pattern.palette.by_code(code)
