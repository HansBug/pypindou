import pytest
from PIL import Image

from pypindou import generate_pattern


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
