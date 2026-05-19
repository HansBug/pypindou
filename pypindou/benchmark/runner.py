"""
Small benchmark helpers for pattern-generation experiments.

Benchmarks in this module intentionally reuse the public
:func:`pypindou.pattern.generate_pattern` API.  They are useful for comparing
image size, palette size, color limits, and quantization strategies without
introducing a separate CLI.

Example::

    >>> from pypindou.benchmark.runner import results_to_rows
    >>> results_to_rows([])
    []
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Union

from pypindou.pattern import generate_pattern


@dataclass(frozen=True)
class BenchmarkCase:
    """
    One benchmark case.

    :param image: Source image path.
    :type image: Union[str, pathlib.Path]
    :param palette: Built-in palette id.
    :type palette: str
    :param width: Target bead-grid width.
    :type width: int
    :param height: Target bead-grid height.
    :type height: int
    :param max_colors: Optional maximum color count, defaults to ``None``.
    :type max_colors: Optional[int], optional
    :param quantize: Quantization method, defaults to ``"nearest"``.
    :type quantize: str, optional
    """

    image: Union[str, Path]
    palette: str
    width: int
    height: int
    max_colors: Optional[int] = None
    quantize: str = "nearest"


@dataclass(frozen=True)
class BenchmarkResult:
    """
    One benchmark result row.

    :param image: Source image path as text.
    :type image: str
    :param palette: Built-in palette id.
    :type palette: str
    :param width: Target bead-grid width.
    :type width: int
    :param height: Target bead-grid height.
    :type height: int
    :param max_colors: Optional maximum color count.
    :type max_colors: Optional[int]
    :param quantize: Quantization method.
    :type quantize: str
    :param bead_count: Number of active beads.
    :type bead_count: int
    :param used_colors: Number of colors used by the generated pattern.
    :type used_colors: int
    :param mean_error: Mean active-pixel quantization error.
    :type mean_error: float
    :param elapsed: Average elapsed seconds.
    :type elapsed: float
    """

    image: str
    palette: str
    width: int
    height: int
    max_colors: Optional[int]
    quantize: str
    bead_count: int
    used_colors: int
    mean_error: float
    elapsed: float


def run_benchmark(cases: Iterable[BenchmarkCase], *, repeat: int = 1) -> List[BenchmarkResult]:
    """
    Run pattern-generation benchmarks.

    :param cases: Benchmark cases to execute.
    :type cases: Iterable[BenchmarkCase]
    :param repeat: Number of times to run each case, defaults to ``1``.
    :type repeat: int, optional
    :return: Benchmark results in input order.
    :rtype: List[BenchmarkResult]
    :raises ValueError: If ``repeat`` is not positive.
    """

    if repeat <= 0:
        raise ValueError("repeat should be positive.")

    results: List[BenchmarkResult] = []
    for case in cases:
        elapsed_total = 0.0
        pattern = None
        for _ in range(repeat):
            start = time.perf_counter()
            pattern = generate_pattern(
                case.image,
                palette=case.palette,
                width=case.width,
                height=case.height,
                max_colors=case.max_colors,
                quantize=case.quantize,  # type: ignore[arg-type]
            )
            elapsed_total += time.perf_counter() - start

        assert pattern is not None
        active_error = pattern.error[pattern.active_mask]
        results.append(
            BenchmarkResult(
                image=str(case.image),
                palette=case.palette,
                width=case.width,
                height=case.height,
                max_colors=case.max_colors,
                quantize=case.quantize,
                bead_count=pattern.bead_count,
                used_colors=len(pattern.color_counts()),
                mean_error=float(active_error.mean()) if len(active_error) else 0.0,
                elapsed=elapsed_total / repeat,
            )
        )
    return results


def results_to_rows(results: Sequence[BenchmarkResult]) -> List[dict]:
    """
    Convert benchmark results to dictionaries.

    :param results: Benchmark result objects.
    :type results: Sequence[BenchmarkResult]
    :return: Shallow dictionary rows.
    :rtype: List[dict]
    """

    return [result.__dict__.copy() for result in results]
