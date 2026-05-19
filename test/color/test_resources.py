import pytest

from pypindou import get_palette, list_palettes
from pypindou.color.resources import _registry


@pytest.mark.unittest
def test_list_palettes():
    palettes = list_palettes()
    ids = {item["id"] for item in palettes}
    assert "mard-221-alfonse-doudou" in ids
    assert "beadcolors-perler" in ids
    assert next(item for item in palettes if item["id"] == "mard-221-alfonse-doudou")["standard"] == "domestic"
    assert next(item for item in palettes if item["id"] == "beadcolors-perler")["standard"] == "international"


@pytest.mark.unittest
def test_load_palette():
    palette = get_palette("mard-221-alfonse-doudou")
    assert palette.size == 221
    assert palette.standard == "domestic"
    assert palette.source_id == "pindou-color-data"
    assert palette.by_code("A1").rgb == (250, 245, 205)


@pytest.mark.unittest
def test_unidentified_filter():
    palette = get_palette("panpan-289")
    palette_with_unknown = get_palette("panpan-289", allow_unidentified=True)
    assert palette.size == 285
    assert palette_with_unknown.size == 289
    assert any(color.unidentified for color in palette_with_unknown.colors)


@pytest.mark.unittest
def test_resource_schema_is_uniform():
    data = _registry()
    assert data["schema"] == "pypindou-palettes"
    assert data["version"] == 2
    assert data["primary_standard"] == "domestic"
    assert data["default_palette"] == "mard-221-alfonse-doudou"

    palette_keys = set(data["palettes"][0])
    color_keys = set(data["palettes"][0]["colors"][0])
    standards = {item["standard"] for item in data["palettes"]}
    assert standards == {"domestic", "international"}

    for item in data["palettes"]:
        assert set(item) == palette_keys
        for color in item["colors"]:
            assert set(color) == color_keys


@pytest.mark.unittest
def test_international_palette_uses_same_dataclasses():
    palette = get_palette("beadcolors-perler")
    assert palette.standard == "international"
    assert palette.source_id == "beadcolors"
    color = palette.colors[0]
    assert color.code
    assert color.hex.startswith("#")
    assert "hsl" in color.metadata
    assert "lab" in color.metadata
