"""
Build README example images from classic scikit-image sample data.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from skimage import data

PROJECT_DIR = Path(__file__).resolve().parents[1]

from pypindou import generate_pattern


ASSET_DIR = PROJECT_DIR / "docs" / "source" / "_static" / "readme"


def _save_source(name: str, image: Image.Image) -> Path:
    path = ASSET_DIR / f"{name}-source.png"
    image.save(path)
    return path


def _build_example(name: str, image: Image.Image, width: int, height: int, max_colors: int) -> None:
    pattern = generate_pattern(
        image,
        width=width,
        height=height,
        palette="mard-221-alfonse-doudou",
        fit="cover",
        max_colors=max_colors,
        quantize="floyd-steinberg",
        color_space="lab",
    )
    _save_source(name, image.resize((width * 8, height * 8)))
    pattern.to_image(scale=8, grid=False).save(ASSET_DIR / f"{name}-preview.png")
    pattern.to_symbol_image(cell_size=18).save(ASSET_DIR / f"{name}-symbols.png")


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    _build_example("astronaut", Image.fromarray(data.astronaut()), width=48, height=48, max_colors=36)
    _build_example("camera", Image.fromarray(data.camera()).convert("RGB"), width=48, height=48, max_colors=24)


if __name__ == "__main__":
    main()
