from __future__ import annotations

import math
import statistics
import time
from dataclasses import dataclass
from typing import Any, Callable

import psutil


@dataclass(frozen=True)
class BenchmarkResult:
    """Summary of a measured benchmark run."""

    mode: str
    iterations: int
    warmup_iterations: int
    total_ms: float
    mean_ms: float
    median_ms: float
    p95_ms: float
    min_ms: float
    max_ms: float
    throughput_ops_s: float | None
    cpu_time_ms: float
    process_rss_peak_mb: float
    samples_ms: tuple[float, ...]

    def as_dict(self, *, include_samples: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {
            "mode": self.mode,
            "iterations": self.iterations,
            "warmup_iterations": self.warmup_iterations,
            "total_ms": self.total_ms,
            "mean_ms": self.mean_ms,
            "median_ms": self.median_ms,
            "p95_ms": self.p95_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "throughput_ops_s": self.throughput_ops_s,
            "cpu_time_ms": self.cpu_time_ms,
            "process_rss_peak_mb": self.process_rss_peak_mb,
        }
        if include_samples:
            result["samples_ms"] = list(self.samples_ms)
        return result


class BenchmarkRunner:
    """Measure repeated execution of a prepared Intelligent Contract operation.

    Deployment/setup is intentionally outside the measured operation so benchmark
    samples represent the contract method itself. For studio mode this still
    includes the configured RPC/wait/consensus path used by the supplied
    operation.
    """

    def __init__(self, operation: Callable[[], Any], *, mode: str) -> None:
        if mode not in {"direct", "studio"}:
            raise ValueError("mode must be 'direct' or 'studio'")
        self._operation = operation
        self._mode = mode

    def run(
        self,
        *,
        iterations: int = 100,
        warmup_iterations: int = 3,
    ) -> BenchmarkResult:
        if iterations <= 0:
            raise ValueError("iterations must be greater than zero")
        if warmup_iterations < 0:
            raise ValueError("warmup_iterations cannot be negative")

        for _ in range(warmup_iterations):
            self._operation()

        process = psutil.Process()
        samples_ms: list[float] = []
        rss_peak = process.memory_info().rss
        cpu_before = process.cpu_times()

        for _ in range(iterations):
            started_ns = time.perf_counter_ns()
            self._operation()
            finished_ns = time.perf_counter_ns()
            samples_ms.append((finished_ns - started_ns) / 1_000_000)
            rss_peak = max(rss_peak, process.memory_info().rss)

        cpu_after = process.cpu_times()

        total_ms = sum(samples_ms)
        total_seconds = total_ms / 1_000
        sorted_samples = sorted(samples_ms)
        p95_index = max(0, math.ceil(len(sorted_samples) * 0.95) - 1)
        cpu_time_ms = (
            (cpu_after.user - cpu_before.user)
            + (cpu_after.system - cpu_before.system)
        ) * 1_000

        return BenchmarkResult(
            mode=self._mode,
            iterations=iterations,
            warmup_iterations=warmup_iterations,
            total_ms=total_ms,
            mean_ms=statistics.mean(samples_ms),
            median_ms=statistics.median(samples_ms),
            p95_ms=sorted_samples[p95_index],
            min_ms=min(samples_ms),
            max_ms=max(samples_ms),
            throughput_ops_s=(iterations / total_seconds) if total_seconds > 0 else None,
            cpu_time_ms=cpu_time_ms,
            process_rss_peak_mb=rss_peak / (1024 * 1024),
            samples_ms=tuple(samples_ms),
        )
