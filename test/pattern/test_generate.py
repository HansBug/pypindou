import pytest
from PIL import Image

from pypindou import generate_pattern
from pypindou.color import BeadColor, Palette
from pypindou.pattern import Pattern

import numpy as np


@pytest.mark.unittest
def test_generate_pattern():
    image = Image.new("RGB", (8, 8), "white")
    for x in range(4):
        for y in range(8):
            image.putpixel((x, y), (240, 10, 10))

    pattern = generate_pattern(
        image,
        width=8,
        height=8,
        palette="mard-221-alfonse-doudou",
        max_colors=8,
        color_space="rgb",
    )
    assert pattern.width == 8
    assert pattern.height == 8
    assert pattern.bead_count == 64
    assert len(pattern.color_counts()) <= 8
    assert pattern.to_image(scale=4).size == (32, 32)
    assert pattern.to_symbol_image(cell_size=8).size == (64, 64)
    assert pattern.to_dict()["legend"]


@pytest.mark.unittest
def test_generate_transparent_pattern():
    image = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    image.putpixel((0, 0), (255, 0, 0, 255))
    pattern = generate_pattern(image, width=4, height=4, background="transparent", color_space="rgb")
    assert pattern.bead_count == 1


@pytest.mark.unittest
def test_generate_pattern_with_cleaning_options():
    image = Image.new("RGB", (8, 8), "white")
    for x in range(4):
        for y in range(8):
            image.putpixel((x, y), (240, 10, 10))

    pattern = generate_pattern(
        image,
        width=8,
        height=8,
        palette="mard-221-alfonse-doudou",
        max_colors=6,
        prefilter="smooth",
        prefilter_radius=0.6,
        contrast=1.1,
        saturation=0.9,
        cleanup="majority",
        cleanup_passes=1,
        min_region_size=2,
        color_space="rgb",
    )
    assert pattern.metadata["prefilter"] == "smooth"
    assert pattern.metadata["cleanup"] == "majority"
    assert len(pattern.color_counts()) <= 6


@pytest.mark.unittest
def test_symbol_image_fits_long_codes(tmp_path):
    palette = Palette(
        "demo",
        "Demo",
        (
            BeadColor("LONG-COLOR-CODE-001", (255, 255, 255)),
            BeadColor("DARK-COLOR-CODE-002", (0, 0, 0)),
        ),
    )
    pattern = Pattern(
        2,
        1,
        palette,
        np.array([[-1, 0]]),
        np.array([[[255, 255, 255], [255, 255, 255]]], dtype=np.uint8),
        np.array([[False, True]]),
        np.zeros((1, 2)),
    )

    image = pattern.to_symbol_image(cell_size=8)
    assert image.size == (16, 8)

    # The renderer must leave the grid boundary and the neighbor cell intact.
    # If the right-side long label spills left, these white interior pixels
    # will be contaminated by black text.
    assert all(image.getpixel((8, y)) == (80, 80, 80) for y in range(8))
    assert all(image.getpixel((x, y)) == (255, 255, 255) for x in range(1, 7) for y in range(1, 7))

    png_path = pattern.save_symbol_chart(tmp_path / "symbols.png", cell_size=8)
    assert png_path.exists()


@pytest.mark.unittest
def test_symbol_svg_export(tmp_path):
    image = Image.new("RGB", (2, 1), "white")
    image.putpixel((1, 0), (0, 0, 0))
    pattern = generate_pattern(image, width=2, height=1, palette="mard-221-alfonse-doudou", color_space="rgb")

    svg = pattern.to_symbol_svg(cell_size=12)
    assert svg.startswith("<?xml")
    assert "<svg" in svg
    assert "<clipPath" in svg
    assert 'textLength="' in svg
    assert 'lengthAdjust="spacingAndGlyphs"' in svg

    svg_path = pattern.save_symbol_chart(tmp_path / "symbols.svg", cell_size=12)
    assert svg_path.read_text(encoding="utf-8") == svg

    with pytest.raises(ValueError):
        pattern.to_symbol_svg(label_mode="bad")

    with pytest.raises(ValueError):
        pattern.save_symbol_chart(tmp_path / "symbols.txt")
