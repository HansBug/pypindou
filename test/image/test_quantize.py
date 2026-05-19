import numpy as np
import pytest

from pypindou.color import BeadColor, Palette
from pypindou.image import quantize_image, reduce_palette_for_image


@pytest.fixture()
def simple_palette():
    return Palette(
        id="simple",
        title="Simple",
        colors=(
            BeadColor("R", (255, 0, 0)),
            BeadColor("G", (0, 255, 0)),
            BeadColor("B", (0, 0, 255)),
        ),
    )


@pytest.mark.unittest
def test_quantize_nearest(simple_palette):
    rgb = np.array([[[250, 1, 2], [1, 2, 250]]], dtype=np.uint8)
    active = np.ones((1, 2), dtype=bool)
    result = quantize_image(rgb, active, simple_palette, color_space="rgb")
    assert result.indices.tolist() == [[0, 2]]


@pytest.mark.unittest
def test_reduce_palette(simple_palette):
    rgb = np.zeros((4, 4, 3), dtype=np.uint8)
    rgb[:2, :] = (255, 0, 0)
    rgb[2:, :] = (0, 255, 0)
    active = np.ones((4, 4), dtype=bool)
    reduced = reduce_palette_for_image(rgb, active, simple_palette, max_colors=2, color_space="rgb")
    assert reduced.size == 2
