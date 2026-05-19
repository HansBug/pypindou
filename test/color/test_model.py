import pytest

from pypindou.color import BeadColor, Palette, hex_to_rgb, rgb_to_hex


@pytest.mark.unittest
def test_rgb_hex():
    assert rgb_to_hex((1, 2, 255)) == "#0102FF"
    assert hex_to_rgb("#0102ff") == (1, 2, 255)


@pytest.mark.unittest
def test_palette_filter():
    palette = Palette(
        id="test",
        title="Test",
        colors=(
            BeadColor("A1", (1, 2, 3)),
            BeadColor("A2", (4, 5, 6), unidentified=True),
            BeadColor("A3", (7, 8, 9)),
        ),
    )

    assert [c.code for c in palette.filter().colors] == ["A1", "A3"]
    assert [c.code for c in palette.filter(allow_unidentified=True).colors] == ["A1", "A2", "A3"]
    assert [c.code for c in palette.filter(include_codes=["A3", "A1"]).colors] == ["A1", "A3"]
    assert palette.by_code("A1").rgb == (1, 2, 3)


@pytest.mark.unittest
def test_palette_duplicate():
    with pytest.raises(ValueError):
        Palette(
            id="test",
            title="Test",
            colors=(BeadColor("A1", (1, 2, 3)), BeadColor("A1", (4, 5, 6))),
        )
