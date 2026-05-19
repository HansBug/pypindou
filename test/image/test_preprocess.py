import numpy as np
import pytest
from PIL import Image

from pypindou.image import load_image, resize_image, rgba_to_rgb_array


@pytest.mark.unittest
def test_load_and_resize():
    image = Image.new("RGBA", (10, 20), (255, 0, 0, 255))
    loaded = load_image(image)
    resized = resize_image(loaded, (5, 5), fit="contain")
    assert resized.size == (5, 5)


@pytest.mark.unittest
def test_rgba_to_rgb_array():
    image = Image.new("RGBA", (2, 1), (255, 0, 0, 255))
    image.putpixel((1, 0), (0, 0, 255, 0))
    rgb, active = rgba_to_rgb_array(image, background="transparent")
    assert rgb.shape == (1, 2, 3)
    assert active.tolist() == [[True, False]]

    white_rgb, white_active = rgba_to_rgb_array(image, background="white")
    assert white_active.tolist() == [[True, True]]
    assert np.array_equal(white_rgb[0, 1], np.array([255, 255, 255], dtype=np.uint8))
