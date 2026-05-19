import pytest

from pypindou import get_palette, list_palettes


@pytest.mark.unittest
def test_list_palettes():
    palettes = list_palettes()
    ids = {item["id"] for item in palettes}
    assert "mard-221-alfonse-doudou" in ids
    assert "beadcolors-perler" in ids


@pytest.mark.unittest
def test_load_palette():
    palette = get_palette("mard-221-alfonse-doudou")
    assert palette.size == 221
    assert palette.by_code("A1").rgb == (250, 245, 205)


@pytest.mark.unittest
def test_unidentified_filter():
    palette = get_palette("panpan-289")
    palette_with_unknown = get_palette("panpan-289", allow_unidentified=True)
    assert palette.size == 285
    assert palette_with_unknown.size == 289
    assert any(color.unidentified for color in palette_with_unknown.colors)
