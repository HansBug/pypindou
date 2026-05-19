"""
Build packaged palette resources from data submodules.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


BEADCOLORS_TITLES = {
    "artkal_a": "Artkal A",
    "artkal_c": "Artkal C",
    "artkal_m": "Artkal M",
    "artkal_r": "Artkal R",
    "artkal_s": "Artkal S",
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


def _load_pindou_palette(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    colors = []
    for raw in data["colors"]:
        rgb = raw.get("rgb")
        if rgb is None:
            continue
        item = {
            "code": raw["code"],
            "name": raw.get("name") or raw["code"],
            "rgb": [int(v) for v in rgb],
            "hex": raw.get("hex") or _hex_from_rgb(rgb),
            "group": raw.get("group"),
            "source": raw.get("source"),
        }
        if raw.get("unidentified"):
            item["unidentified"] = True
        if raw.get("original_code") is not None:
            item["original_code"] = raw.get("original_code")
        if raw.get("notes"):
            item["notes"] = raw.get("notes")
        colors.append(item)

    return {
        "id": data["id"],
        "title": data["title"],
        "description": data.get("description"),
        "source": "HansBug/pindou-color-data",
        "count": len(colors),
        "metadata": {
            "upstream_schema": data.get("schema"),
            "market": data.get("market"),
            "groups": data.get("groups"),
        },
        "colors": colors,
    }


def _load_beadcolors_palette(path: Path, source_id: str) -> Dict[str, Any]:
    colors = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            code, name, symbol, r, g, b, *rest = row
            rgb = [int(float(r)), int(float(g)), int(float(b))]
            colors.append(
                {
                    "code": code,
                    "name": name,
                    "symbol": symbol,
                    "rgb": rgb,
                    "hex": _hex_from_rgb(rgb),
                    "source": rest[-1] if rest else None,
                }
            )

    return {
        "id": f"beadcolors-{source_id}",
        "title": BEADCOLORS_TITLES.get(source_id, source_id.replace("_", " ").title()),
        "description": f"{BEADCOLORS_TITLES.get(source_id, source_id)} palette from maxcleme/beadcolors gen/v3.",
        "source": "maxcleme/beadcolors",
        "count": len(colors),
        "metadata": {
            "upstream_file": f"gen/v3/{source_id}.csv",
        },
        "colors": colors,
    }


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
        "version": 1,
        "sources": [
            {
                "id": "pindou-color-data",
                "url": "https://github.com/HansBug/pindou-color-data",
            },
            {
                "id": "beadcolors",
                "url": "https://github.com/maxcleme/beadcolors",
            },
        ],
        "palettes": sorted(palettes, key=lambda item: item["id"]),
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
