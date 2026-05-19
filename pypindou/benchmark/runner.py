"""
Small benchmark helpers for pattern-generation experiments.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from pypindou.pattern import generate_pattern


@dataclass(frozen=True)
class BenchmarkCase:
    """
    One benchmark case.
    """

    image: str | Path
    palette: str
    width: int
    height: int
    max_colors: int | None = None
    quantize: str = "nearest"


@dataclass(frozen=True)
class BenchmarkResult:
    """
    One benchmark result row.
    """

    image: str
    palette: str
    width: int
    height: int
    max_colors: int | None
    quantize: str
    bead_count: int
    used_colors: int
    mean_error: float
    elapsed: float


def run_benchmark(cases: Iterable[BenchmarkCase], *, repeat: int = 1) -> List[BenchmarkResult]:
    """
    Run pattern-generation benchmarks.
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
    """

    return [result.__dict__.copy() for result in results]
