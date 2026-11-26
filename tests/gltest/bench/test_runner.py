from types import SimpleNamespace

import pytest

from gltest.bench import BenchmarkRunner
import gltest.bench.runner as runner_module


class _FakeProcess:
    def __init__(self):
        self._rss = iter(
            [
                10 * 1024 * 1024,
                20 * 1024 * 1024,
                30 * 1024 * 1024,
                25 * 1024 * 1024,
            ]
        )
        self._cpu = iter(
            [
                SimpleNamespace(user=1.0, system=2.0),
                SimpleNamespace(user=1.004, system=2.002),
            ]
        )

    def memory_info(self):
        return SimpleNamespace(rss=next(self._rss))

    def cpu_times(self):
        return next(self._cpu)


def test_benchmark_runner_reports_latency_throughput_and_resources(monkeypatch):
    timestamps = iter(
        [
            0,
            1_000_000,
            1_000_000,
            3_000_000,
            3_000_000,
            6_000_000,
        ]
    )
    calls = []

    monkeypatch.setattr(runner_module.time, "perf_counter_ns", lambda: next(timestamps))
    monkeypatch.setattr(runner_module.psutil, "Process", _FakeProcess)

    result = BenchmarkRunner(lambda: calls.append("call"), mode="direct").run(
        iterations=3,
        warmup_iterations=0,
    )

    assert calls == ["call", "call", "call"]
    assert result.samples_ms == (1.0, 2.0, 3.0)
    assert result.total_ms == 6.0
    assert result.mean_ms == 2.0
    assert result.median_ms == 2.0
    assert result.p95_ms == 3.0
    assert result.min_ms == 1.0
    assert result.max_ms == 3.0
    assert result.throughput_ops_s == pytest.approx(500.0)
    assert result.cpu_time_ms == pytest.approx(6.0)
    assert result.process_rss_peak_mb == 30.0


def test_benchmark_runner_warms_up_before_measurement(monkeypatch):
    timestamps = iter([0, 1_000_000])
    calls = []

    fake_process = _FakeProcess()
    monkeypatch.setattr(runner_module.time, "perf_counter_ns", lambda: next(timestamps))
    monkeypatch.setattr(runner_module.psutil, "Process", lambda: fake_process)

    BenchmarkRunner(lambda: calls.append("call"), mode="studio").run(
        iterations=1,
        warmup_iterations=2,
    )

    assert calls == ["call", "call", "call"]


@pytest.mark.parametrize(
    ("iterations", "warmup_iterations", "message"),
    [
        (0, 0, "iterations"),
        (-1, 0, "iterations"),
        (1, -1, "warmup_iterations"),
    ],
)
def test_benchmark_runner_rejects_invalid_counts(
    iterations,
    warmup_iterations,
    message,
):
    with pytest.raises(ValueError, match=message):
        BenchmarkRunner(lambda: None, mode="direct").run(
            iterations=iterations,
            warmup_iterations=warmup_iterations,
        )


def test_result_dict_samples_are_opt_in(monkeypatch):
    timestamps = iter([0, 1_000_000])
    fake_process = _FakeProcess()
    monkeypatch.setattr(runner_module.time, "perf_counter_ns", lambda: next(timestamps))
    monkeypatch.setattr(runner_module.psutil, "Process", lambda: fake_process)

    result = BenchmarkRunner(lambda: None, mode="direct").run(
        iterations=1,
        warmup_iterations=0,
    )

    assert "samples_ms" not in result.as_dict()
    assert result.as_dict(include_samples=True)["samples_ms"] == [1.0]


def test_zero_duration_uses_json_safe_null_throughput(monkeypatch):
    timestamps = iter([0, 0])
    fake_process = _FakeProcess()
    monkeypatch.setattr(runner_module.time, "perf_counter_ns", lambda: next(timestamps))
    monkeypatch.setattr(runner_module.psutil, "Process", lambda: fake_process)

    result = BenchmarkRunner(lambda: None, mode="direct").run(
        iterations=1,
        warmup_iterations=0,
    )

    assert result.total_ms == 0.0
    assert result.throughput_ops_s is None
    assert result.as_dict()["throughput_ops_s"] is None
