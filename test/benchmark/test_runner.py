import pytest
from PIL import Image

from pypindou.benchmark import BenchmarkCase, results_to_rows, run_benchmark


@pytest.mark.unittest
def test_run_benchmark(tmp_path):
    image_path = tmp_path / "image.png"
    Image.new("RGB", (8, 8), "red").save(image_path)

    results = run_benchmark(
        [
            BenchmarkCase(
                image=image_path,
                palette="mard-221-alfonse-doudou",
                width=8,
                height=8,
                max_colors=4,
            )
        ]
    )
    assert len(results) == 1
    assert results[0].bead_count == 64
    assert results_to_rows(results)[0]["palette"] == "mard-221-alfonse-doudou"
