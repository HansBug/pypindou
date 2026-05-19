"""
Palette and bead-color data models.

This module defines the shared schema used for domestic and international bead
palette resources.  Resource builders normalize upstream data into
:class:`BeadColor` and :class:`Palette`, while pattern generation consumes the
same objects for color matching and reporting.

Example::

    >>> from pypindou.color.model import BeadColor, Palette
    >>> palette = Palette("demo", "Demo", (BeadColor("001", (255, 255, 255)),))
    >>> palette.size
    1
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

    :param rgb: Three RGB channel values in ``0..255``.
    :type rgb: Sequence[int]
    :return: Uppercase hex color string.
    :rtype: str
    :raises ValueError: If ``rgb`` does not contain exactly three valid
        channel values.

    Example::

        >>> rgb_to_hex((255, 128, 0))
        '#FF8000'
    """

    r, g, b = _check_rgb(rgb)
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def hex_to_rgb(value: str) -> RGB:
    """
    Convert ``#RRGGBB`` or ``RRGGBB`` to an RGB triplet.

    :param value: Hex color text.
    :type value: str
    :return: RGB tuple.
    :rtype: RGB
    :raises ValueError: If the input is not a six-digit hex color.

    Example::

        >>> hex_to_rgb("#FF8000")
        (255, 128, 0)
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

    :param code: Palette-specific bead code.
    :type code: str
    :param rgb: RGB channel tuple in ``0..255``.
    :type rgb: RGB
    :param name: Human-readable color name, defaults to ``None``.
    :type name: Optional[str], optional
    :param hex: Hex color string. When omitted it is derived from ``rgb``.
    :type hex: Optional[str], optional
    :param group: Optional upstream color group.
    :type group: Optional[str], optional
    :param source: Optional source label.
    :type source: Optional[str], optional
    :param unidentified: Whether upstream marks the color as unidentified,
        defaults to ``False``.
    :type unidentified: bool, optional
    :param original_code: Raw upstream code before normalization, defaults to
        ``None``.
    :type original_code: Optional[str], optional
    :param metadata: Extra normalized upstream fields.
    :type metadata: Mapping[str, Any], optional

    Example::

        >>> BeadColor("001", (255, 255, 255)).hex
        '#FFFFFF'
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

        :return: Dictionary representation using plain JSON-compatible values.
        :rtype: Dict[str, Any]
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

    :param id: Stable palette id.
    :type id: str
    :param title: Human-readable palette title.
    :type title: str
    :param colors: Palette colors in source order.
    :type colors: Tuple[BeadColor, ...]
    :param description: Optional palette description, defaults to ``None``.
    :type description: Optional[str], optional
    :param standard: Palette standard, usually ``"domestic"`` or
        ``"international"``, defaults to ``"domestic"``.
    :type standard: str, optional
    :param source: Optional source family.
    :type source: Optional[str], optional
    :param source_id: Optional upstream source id.
    :type source_id: Optional[str], optional
    :param source_url: Optional upstream URL.
    :type source_url: Optional[str], optional
    :param metadata: Extra palette metadata.
    :type metadata: Mapping[str, Any], optional
    :raises ValueError: If no colors are provided or color codes are duplicated.

    Example::

        >>> Palette("demo", "Demo", (BeadColor("001", (1, 2, 3)),)).by_code("001").rgb
        (1, 2, 3)
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

        :return: Palette size.
        :rtype: int
        """

        return len(self.colors)

    def by_code(self, code: str) -> BeadColor:
        """
        Get a color by code.

        :param code: Palette-specific bead code.
        :type code: str
        :return: Matching bead color.
        :rtype: BeadColor
        :raises KeyError: If the code does not exist in this palette.
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

        :param include_codes: Optional allow-list of color codes.
        :type include_codes: Optional[Iterable[str]], optional
        :param exclude_codes: Optional deny-list of color codes.
        :type exclude_codes: Optional[Iterable[str]], optional
        :param allow_unidentified: Whether to keep colors marked
            ``unidentified``, defaults to ``False``.
        :type allow_unidentified: bool, optional
        :param max_colors: Maximum number of colors to keep after filtering,
            defaults to ``None``.
        :type max_colors: Optional[int], optional
        :return: Filtered palette.
        :rtype: Palette
        :raises ValueError: If ``max_colors`` is not positive.
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

        :return: Dictionary representation using plain JSON-compatible values.
        :rtype: Dict[str, Any]
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
