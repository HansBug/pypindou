"""
Pattern model.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from pypindou.color import BeadColor, Palette


@dataclass(frozen=True)
class Pattern:
    """
    A bead pattern generated from one image.
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
        """

        return int(self.active_mask.sum())

    @property
    def board_size(self) -> Tuple[int, int]:
        """
        Pattern grid size as ``(width, height)``.
        """

        return self.width, self.height

    def color_counts(self) -> Dict[str, int]:
        """
        Count beads by color code.
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

    def to_symbol_image(self, *, cell_size: int = 24, show_grid: bool = True) -> Image.Image:
        """
        Render a symbol map with bead codes.
        """

        if cell_size <= 0:
            raise ValueError("cell_size should be positive.")

        canvas = Image.new("RGB", (self.width * cell_size, self.height * cell_size), "white")
        draw = ImageDraw.Draw(canvas)
        font = ImageFont.load_default()
        for y in range(self.height):
            for x in range(self.width):
                left, top = x * cell_size, y * cell_size
                box = (left, top, left + cell_size, top + cell_size)
                if self.active_mask[y, x] and self.indices[y, x] >= 0:
                    color = self.palette.colors[int(self.indices[y, x])]
                    draw.rectangle(box, fill=color.rgb)
                    luminance = 0.2126 * color.rgb[0] + 0.7152 * color.rgb[1] + 0.0722 * color.rgb[2]
                    text_color = (0, 0, 0) if luminance > 150 else (255, 255, 255)
                    label = color.code[-3:]
                    bbox = draw.textbbox((0, 0), label, font=font)
                    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                    draw.text((left + (cell_size - tw) / 2, top + (cell_size - th) / 2), label, fill=text_color, font=font)
                if show_grid:
                    draw.rectangle(box, outline=(80, 80, 80))
        return canvas


def color_for_code(pattern: Pattern, code: str) -> BeadColor:
    """
    Return the palette color for ``code`` in a pattern.
    """

    return pattern.palette.by_code(code)
