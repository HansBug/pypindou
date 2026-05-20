"""
Build README example images from fixed anime pixel-art references.
"""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

PROJECT_DIR = Path(__file__).resolve().parents[1]

from pypindou import generate_pattern
from pypindou.image import resize_image


ASSET_DIR = PROJECT_DIR / "docs" / "source" / "_static" / "readme"


@dataclass(frozen=True)
class ReadmeExample:
    """
    Configuration for one README image example.

    :param name: Stable asset name prefix.
    :type name: str
    :param original_filename: Local source image filename.
    :type original_filename: str
    :param image_url: Fallback source image URL.
    :type image_url: str
    :param width: Pattern width in beads.
    :type width: int
    :param height: Pattern height in beads.
    :type height: int
    :param max_colors: Maximum number of bead colors.
    :type max_colors: int
    """

    name: str
    original_filename: str
    image_url: str
    width: int
    height: int
    max_colors: int


EXAMPLES = (
    ReadmeExample(
        name="koishi",
        original_filename="koishi-source-original.png",
        image_url="https://cdn.donmai.us/original/05/54/0554904328656f8d14591a4efcc1fa09.png",
        width=48,
        height=48,
        max_colors=22,
    ),
    ReadmeExample(
        name="marisa",
        original_filename="marisa-source-original.jpg",
        image_url="https://cdn.donmai.us/sample/ad/70/sample-ad70765bf4e3e8333bd74ea980f62e41.jpg",
        width=58,
        height=33,
        max_colors=18,
    ),
)


def _source_path(example: ReadmeExample) -> Path:
    """
    Get the local source image path for an example.

    :param example: README example configuration.
    :type example: ReadmeExample
    :return: Local source path.
    :rtype: pathlib.Path
    """

    return ASSET_DIR / example.original_filename


def _ensure_source(example: ReadmeExample) -> Path:
    """
    Ensure a README source image exists locally.

    :param example: README example configuration.
    :type example: ReadmeExample
    :return: Local source path.
    :rtype: pathlib.Path
    """

    path = _source_path(example)
    if not path.exists():
        urllib.request.urlretrieve(example.image_url, path)
    return path


def _white_background(image: Image.Image) -> Image.Image:
    """
    Composite an image over white for README display.

    :param image: Source image.
    :type image: PIL.Image.Image
    :return: RGB image composited over white.
    :rtype: PIL.Image.Image
    """

    src = image.convert("RGBA")
    canvas = Image.new("RGBA", src.size, (255, 255, 255, 255))
    canvas.alpha_composite(src)
    return canvas.convert("RGB")


def _save_source(example: ReadmeExample, image: Image.Image, *, scale: int) -> Path:
    """
    Save a source-image thumbnail aligned to the generated bead grid.

    :param example: README example configuration.
    :type example: ReadmeExample
    :param image: Source image.
    :type image: PIL.Image.Image
    :param scale: Display scale for one bead cell.
    :type scale: int
    :return: Saved image path.
    :rtype: pathlib.Path
    """

    path = ASSET_DIR / f"{example.name}-source.png"
    resized = resize_image(image, (example.width, example.height), fit="contain", resample="nearest")
    _white_background(resized).resize((example.width * scale, example.height * scale), Image.Resampling.NEAREST).save(path)
    return path


def _build_example(example: ReadmeExample) -> None:
    """
    Build all README assets for one example.

    :param example: README example configuration.
    :type example: ReadmeExample
    :return: ``None``.
    :rtype: None
    """

    image = Image.open(_ensure_source(example)).convert("RGBA")
    pattern = generate_pattern(
        image,
        width=example.width,
        height=example.height,
        palette="mard-221-alfonse-doudou",
        fit="contain",
        background="transparent",
        resample="box",
        max_colors=example.max_colors,
        quantize="nearest",
        color_space="lab",
        prefilter="none",
        contrast=1.05,
        saturation=1.04,
        sharpness=1.0,
        cleanup="majority",
        cleanup_passes=1,
        cleanup_threshold=5,
        min_region_size=2,
    )
    _save_source(example, image, scale=6)
    pattern.to_image(scale=6, grid=False).save(ASSET_DIR / f"{example.name}-preview.png")
    pattern.save_symbol_chart(ASSET_DIR / f"{example.name}-symbols.png", cell_size=12)
    pattern.save_symbol_chart(ASSET_DIR / f"{example.name}-symbols.svg", cell_size=12)


def main() -> None:
    """
    Rebuild README example source, preview, and symbol images.

    :return: ``None``.
    :rtype: None
    """

    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for example in EXAMPLES:
        _build_example(example)


if __name__ == "__main__":
    main()
