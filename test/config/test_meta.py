import pytest

from pypindou.config.meta import __AUTHOR__, __TITLE__, __VERSION__


@pytest.mark.unittest
def test_meta():
    assert __TITLE__ == "pypindou"
    assert __VERSION__
    assert __AUTHOR__ == "HansBug"
