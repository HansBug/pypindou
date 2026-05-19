"""
Built-in palette resource loading.

The packaged ``palettes.json`` file is generated from domestic and
international submodules by ``make resource``.  Runtime code should load
palettes through this module instead of reading the resource file directly.

Example::

    >>> from pypindou.color.resources import list_palettes
    >>> isinstance(list_palettes(), list)
    True
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Union

from .model import BeadColor, Palette

try:
    from importlib import resources

    resources.files
except (AttributeError, ImportError):
    import importlib_resources as resources  # type: ignore[no-redef]


def _read_json(name: str) -> Any:
    with resources.files("pypindou.resources").joinpath(name).open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache()
def _registry() -> Dict[str, Any]:
    return _read_json("palettes.json")


def list_palettes() -> List[Dict[str, Any]]:
    """
    List built-in palettes.

    :return: Summary dictionaries for packaged palettes.
    :rtype: List[Dict[str, Any]]
    """

    return [
        {
            "id": item["id"],
            "title": item["title"],
            "count": item["count"],
            "standard": item.get("standard", "domestic"),
            "source": item.get("source"),
            "source_id": item.get("source_id"),
            "description": item.get("description"),
        }
        for item in _registry()["palettes"]
    ]


def load_palette(palette_id: str, *, allow_unidentified: bool = False) -> Palette:
    """
    Load a built-in palette by id.

    :param palette_id: Built-in palette id.
    :type palette_id: str
    :param allow_unidentified: Whether to include colors marked
        ``unidentified``, defaults to ``False``.
    :type allow_unidentified: bool, optional
    :return: Loaded palette.
    :rtype: pypindou.color.Palette
    :raises KeyError: If ``palette_id`` is unknown.
    """

    for item in _registry()["palettes"]:
        if item["id"] == palette_id:
            colors = []
            for raw in item["colors"]:
                if raw.get("unidentified") and not allow_unidentified:
                    continue

                metadata = {
                    key: value
                    for key, value in raw.items()
                    if key
                    not in {
                        "code",
                        "name",
                        "hex",
                        "rgb",
                        "group",
                        "source",
                        "unidentified",
                        "original_code",
                        "metadata",
                    }
                }
                metadata.update(raw.get("metadata") or {})
                colors.append(
                    BeadColor(
                        code=raw["code"],
                        name=raw.get("name"),
                        rgb=tuple(raw["rgb"]),
                        hex=raw.get("hex"),
                        group=raw.get("group"),
                        source=raw.get("source"),
                        unidentified=bool(raw.get("unidentified", False)),
                        original_code=raw.get("original_code"),
                        metadata=metadata,
                    )
                )

            return Palette(
                id=item["id"],
                title=item["title"],
                colors=tuple(colors),
                description=item.get("description"),
                standard=item.get("standard", "domestic"),
                source=item.get("source"),
                source_id=item.get("source_id"),
                source_url=item.get("source_url"),
                metadata=item.get("metadata") or {},
            )

    raise KeyError(f"Built-in palette {palette_id!r} not found.")


def get_palette(
    palette: Union[str, Palette],
    *,
    include_codes: Optional[Iterable[str]] = None,
    exclude_codes: Optional[Iterable[str]] = None,
    allow_unidentified: bool = False,
    max_colors: Optional[int] = None,
) -> Palette:
    """
    Resolve and optionally filter a palette.

    :param palette: Built-in palette id or explicit palette object.
    :type palette: Union[str, pypindou.color.Palette]
    :param include_codes: Optional allow-list of color codes.
    :type include_codes: Optional[Iterable[str]], optional
    :param exclude_codes: Optional deny-list of color codes.
    :type exclude_codes: Optional[Iterable[str]], optional
    :param allow_unidentified: Whether to include colors marked
        ``unidentified``, defaults to ``False``.
    :type allow_unidentified: bool, optional
    :param max_colors: Optional leading color count after filtering.
    :type max_colors: Optional[int], optional
    :return: Resolved palette.
    :rtype: pypindou.color.Palette
    """

    result = load_palette(palette, allow_unidentified=allow_unidentified) if isinstance(palette, str) else palette
    return result.filter(
        include_codes=include_codes,
        exclude_codes=exclude_codes,
        allow_unidentified=allow_unidentified,
        max_colors=max_colors,
    )
