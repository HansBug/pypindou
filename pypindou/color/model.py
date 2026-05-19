"""
Palette and bead-color data models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


RGB = Tuple[int, int, int]


def _check_rgb(rgb: Sequence[int]) -> RGB:
    if len(rgb) != 3:
        raise ValueError("RGB value should contain exactly 3 channels.")

    values = tuple(int(item) for item in rgb)
    for item in values:
        if not 0 <= item <= 255:
            raise ValueError(f"RGB channel should be in [0, 255], but {item!r} found.")
    return values  # type: ignore[return-value]


def rgb_to_hex(rgb: Sequence[int]) -> str:
    """
    Convert an RGB triplet to ``#RRGGBB`` format.
    """

    r, g, b = _check_rgb(rgb)
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def hex_to_rgb(value: str) -> RGB:
    """
    Convert ``#RRGGBB`` or ``RRGGBB`` to an RGB triplet.
    """

    text = value.strip()
    if text.startswith("#"):
        text = text[1:]
    if len(text) != 6:
        raise ValueError(f"Invalid hex color {value!r}.")
    try:
        return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
    except ValueError as err:
        raise ValueError(f"Invalid hex color {value!r}.") from err


@dataclass(frozen=True)
class BeadColor:
    """
    One color entry in a fuse-bead palette.
    """

    code: str
    rgb: RGB
    name: Optional[str] = None
    hex: Optional[str] = None
    group: Optional[str] = None
    source: Optional[str] = None
    unidentified: bool = False
    original_code: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "rgb", _check_rgb(self.rgb))
        object.__setattr__(self, "hex", (self.hex or rgb_to_hex(self.rgb)).upper())

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this color to a JSON-serializable dictionary.
        """

        data: Dict[str, Any] = {
            "code": self.code,
            "name": self.name,
            "rgb": list(self.rgb),
            "hex": self.hex,
            "group": self.group,
            "source": self.source,
            "unidentified": self.unidentified,
            "original_code": self.original_code,
            "metadata": dict(self.metadata),
        }
        return data


@dataclass(frozen=True)
class Palette:
    """
    A named collection of bead colors.
    """

    id: str
    title: str
    colors: Tuple[BeadColor, ...]
    description: Optional[str] = None
    standard: str = "domestic"
    source: Optional[str] = None
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "colors", tuple(self.colors))
        if not self.colors:
            raise ValueError("Palette should contain at least one color.")

        codes = [color.code for color in self.colors]
        if len(codes) != len(set(codes)):
            duplicated = sorted({code for code in codes if codes.count(code) > 1})
            raise ValueError(f"Duplicated color codes in palette {self.id!r}: {duplicated!r}.")

    @property
    def size(self) -> int:
        """
        Number of colors in this palette.
        """

        return len(self.colors)

    def by_code(self, code: str) -> BeadColor:
        """
        Get a color by code.
        """

        index = {color.code: color for color in self.colors}
        try:
            return index[code]
        except KeyError as err:
            raise KeyError(f"Color code {code!r} not found in palette {self.id!r}.") from err

    def filter(
        self,
        *,
        include_codes: Optional[Iterable[str]] = None,
        exclude_codes: Optional[Iterable[str]] = None,
        allow_unidentified: bool = False,
        max_colors: Optional[int] = None,
    ) -> "Palette":
        """
        Return a filtered palette while preserving source order.
        """

        include_set = set(include_codes) if include_codes is not None else None
        exclude_set = set(exclude_codes or ())

        colors: List[BeadColor] = []
        for color in self.colors:
            if include_set is not None and color.code not in include_set:
                continue
            if color.code in exclude_set:
                continue
            if color.unidentified and not allow_unidentified:
                continue
            colors.append(color)

        if max_colors is not None:
            if max_colors <= 0:
                raise ValueError("max_colors should be positive.")
            colors = colors[:max_colors]

        return Palette(
            id=self.id,
            title=self.title,
            colors=tuple(colors),
            description=self.description,
            standard=self.standard,
            source=self.source,
            source_id=self.source_id,
            source_url=self.source_url,
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this palette to a JSON-serializable dictionary.
        """

        data: Dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "standard": self.standard,
            "source": self.source,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "count": len(self.colors),
            "metadata": dict(self.metadata),
            "colors": [color.to_dict() for color in self.colors],
        }
        return data
