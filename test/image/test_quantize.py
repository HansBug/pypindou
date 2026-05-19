import numpy as np
import pytest

from pypindou.color import BeadColor, Palette
from pypindou.image import cleanup_quantization, merge_small_regions, quantize_image, reduce_palette_for_image


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


@pytest.mark.unittest
def test_cleanup_quantization_majority(simple_palette):
    indices = np.array(
        [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
        ],
        dtype=np.int32,
    )
    active = np.ones((3, 3), dtype=bool)
    cleaned = cleanup_quantization(indices, active, passes=1, threshold=5)
    assert cleaned[1, 1] == 1


@pytest.mark.unittest
def test_merge_small_regions(simple_palette):
    indices = np.array(
        [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
        ],
        dtype=np.int32,
    )
    active = np.ones((3, 3), dtype=bool)
    merged = merge_small_regions(indices, active, min_size=2)
    assert merged[1, 1] == 1


@pytest.mark.unittest
def test_quantize_with_cleanup(simple_palette):
    rgb = np.zeros((3, 3, 3), dtype=np.uint8)
    rgb[:, :] = (0, 255, 0)
    rgb[1, 1] = (255, 0, 0)
    active = np.ones((3, 3), dtype=bool)
    result = quantize_image(
        rgb,
        active,
        simple_palette,
        color_space="rgb",
        cleanup="majority",
        cleanup_passes=1,
        cleanup_threshold=5,
    )
    assert result.indices[1, 1] == 1


@pytest.mark.unittest
def test_invalid_cleanup_mode(simple_palette):
    rgb = np.array([[[250, 1, 2]]], dtype=np.uint8)
    active = np.ones((1, 1), dtype=bool)
    with pytest.raises(ValueError):
        quantize_image(rgb, active, simple_palette, color_space="rgb", cleanup="bad")  # type: ignore[arg-type]
