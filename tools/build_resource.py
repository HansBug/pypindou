"""
Build packaged palette resources from data submodules.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


DEFAULT_PALETTE_ID = "mard-221-alfonse-doudou"
DOMESTIC_STANDARD = "domestic"
INTERNATIONAL_STANDARD = "international"

DOMESTIC_SOURCE = {
    "id": "pindou-color-data",
    "name": "HansBug/pindou-color-data",
    "url": "https://github.com/HansBug/pindou-color-data",
    "standard": DOMESTIC_STANDARD,
    "primary": True,
}
INTERNATIONAL_SOURCE = {
    "id": "beadcolors",
    "name": "maxcleme/beadcolors",
    "url": "https://github.com/maxcleme/beadcolors",
    "standard": INTERNATIONAL_STANDARD,
    "primary": False,
}

BEADCOLORS_TITLES = {
    "artkal_a": "Artkal A",
    "artkal_c": "Artkal C",
    "artkal_m": "Artkal M",
    "artkal_r": "Artkal R",
    "artkal_s": "Artkal S",
    "diamondDotz": "Diamond Dotz",
    "hama": "Hama Midi",
    "hama_maxi": "Hama Maxi",
    "hama_mini": "Hama Mini",
    "mard": "Mard",
    "nabbi": "Nabbi",
    "perler": "Perler",
    "perler_caps": "Perler Caps",
    "perler_mini": "Perler Mini",
    "yant": "Yant",
}


def _hex_from_rgb(rgb: Iterable[int]) -> str:
    r, g, b = [int(item) for item in rgb]
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def _hex_value(value: Optional[str], rgb: Iterable[int]) -> str:
    if value:
        text = value.strip()
        if not text.startswith("#"):
            text = f"#{text}"
        return text.upper()
    return _hex_from_rgb(rgb)


def _color_record(
    *,
    code: str,
    name: Optional[str],
    rgb: Iterable[int],
    hex_value: Optional[str] = None,
    group: Optional[str] = None,
    source: Optional[str] = None,
    unidentified: bool = False,
    original_code: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    rgb_values = [int(v) for v in rgb]
    return {
        "code": str(code),
        "name": name,
        "rgb": rgb_values,
        "hex": _hex_value(hex_value, rgb_values),
        "group": group,
        "source": source,
        "unidentified": bool(unidentified),
        "original_code": original_code,
        "metadata": dict(metadata or {}),
    }


def _palette_record(
    *,
    palette_id: str,
    title: str,
    description: Optional[str],
    standard: str,
    source: Mapping[str, Any],
    colors: List[Dict[str, Any]],
    metadata: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "id": palette_id,
        "title": title,
        "description": description,
        "standard": standard,
        "source": source["name"],
        "source_id": source["id"],
        "source_url": source["url"],
        "count": len(colors),
        "metadata": dict(metadata or {}),
        "colors": colors,
    }


def _load_pindou_palette(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    colors = []
    for raw in data["colors"]:
        rgb = raw.get("rgb")
        if rgb is None:
            continue

        metadata = {}
        if raw.get("notes"):
            metadata["notes"] = raw.get("notes")

        colors.append(
            _color_record(
                code=raw["code"],
                name=raw.get("name") or raw["code"],
                rgb=rgb,
                hex_value=raw.get("hex"),
                group=raw.get("group"),
                source=raw.get("source"),
                unidentified=bool(raw.get("unidentified", False)),
                original_code=raw.get("original_code"),
                metadata=metadata,
            )
        )

    return _palette_record(
        palette_id=data["id"],
        title=data["title"],
        description=data.get("description"),
        standard=DOMESTIC_STANDARD,
        source=DOMESTIC_SOURCE,
        colors=colors,
        metadata={
            "upstream_schema": data.get("schema"),
            "generated_at": data.get("generated_at"),
            "market": data.get("market"),
            "groups": data.get("groups"),
            "sources": data.get("sources"),
        },
    )


def _load_beadcolors_palette(path: Path, source_id: str) -> Dict[str, Any]:
    colors = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            code, name, symbol, r, g, b, *rest = row
            rgb = [int(float(r)), int(float(g)), int(float(b))]
            metadata: Dict[str, Any] = {}
            if symbol:
                metadata["symbol"] = symbol
            if len(rest) >= 3:
                metadata["hsl"] = [float(rest[0]), float(rest[1]), float(rest[2])]
            if len(rest) >= 6:
                metadata["lab"] = [float(rest[3]), float(rest[4]), float(rest[5])]
            if len(rest) > 7:
                metadata["extra"] = rest[7:]

            colors.append(
                _color_record(
                    code=code,
                    name=name,
                    rgb=rgb,
                    source=rest[6] if len(rest) >= 7 else None,
                    metadata=metadata,
                )
            )

    title = BEADCOLORS_TITLES.get(source_id, source_id.replace("_", " ").title())
    return _palette_record(
        palette_id=f"beadcolors-{source_id}",
        title=title,
        description=f"{title} palette from maxcleme/beadcolors gen/v3.",
        standard=INTERNATIONAL_STANDARD,
        source=INTERNATIONAL_SOURCE,
        colors=colors,
        metadata={
            "upstream_file": f"gen/v3/{source_id}.csv",
        },
    )


def build_resource(project_dir: Path, output: Path) -> Dict[str, Any]:
    palettes: List[Dict[str, Any]] = []

    pindou_dir = project_dir / "data" / "pindou-color-data"
    for colors_path in sorted(pindou_dir.glob("*/colors.json")):
        palettes.append(_load_pindou_palette(colors_path))

    beadcolors_dir = project_dir / "data" / "beadcolors" / "gen" / "v3"
    for csv_path in sorted(beadcolors_dir.glob("*.csv")):
        palettes.append(_load_beadcolors_palette(csv_path, csv_path.stem))

    ids = [item["id"] for item in palettes]
    if len(ids) != len(set(ids)):
        duplicated = sorted({item for item in ids if ids.count(item) > 1})
        raise ValueError(f"Duplicated palette ids: {duplicated!r}.")

    data = {
        "schema": "pypindou-palettes",
        "version": 2,
        "primary_standard": DOMESTIC_STANDARD,
        "default_palette": DEFAULT_PALETTE_ID,
        "standards": [
            {
                "id": DOMESTIC_STANDARD,
                "title": "Chinese domestic bead palettes",
                "description": "Primary palettes used by pypindou, based on common Chinese fuse-bead color systems.",
                "primary": True,
            },
            {
                "id": INTERNATIONAL_STANDARD,
                "title": "International bead palettes",
                "description": "Supplementary international palettes normalized into the same pypindou resource schema.",
                "primary": False,
            },
        ],
        "sources": [DOMESTIC_SOURCE, INTERNATIONAL_SOURCE],
        "palettes": sorted(palettes, key=lambda item: (item["standard"] != DOMESTIC_STANDARD, item["id"])),
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Build pypindou packaged palette resource.")
    parser.add_argument("-p", "--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("-o", "--output", type=Path, default=Path("pypindou/resources/palettes.json"))
    args = parser.parse_args()

    data = build_resource(args.project_dir.resolve(), args.output)
    print(f"Generated {args.output} with {len(data['palettes'])} palettes.")


if __name__ == "__main__":
    main()
