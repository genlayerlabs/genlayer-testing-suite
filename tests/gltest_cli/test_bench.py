import json
import sys

import pytest

from gltest.bench import BenchmarkResult
import gltest_cli.bench as bench_cli
import gltest_cli.main as cli_main


def _result(mode="direct", throughput=500.0):
    return BenchmarkResult(
        mode=mode,
        iterations=2,
        warmup_iterations=1,
        total_ms=4.0,
        mean_ms=2.0,
        median_ms=2.0,
        p95_ms=3.0,
        min_ms=1.0,
        max_ms=3.0,
        throughput_ops_s=throughput,
        cpu_time_ms=1.0,
        process_rss_peak_mb=42.0,
        samples_ms=(1.0, 3.0),
    )


def test_gltest_keeps_forwarding_non_bench_args_to_pytest(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["gltest", "-q", "tests/gltest/"])
    seen = {}

    def fake_pytest_main():
        seen["called"] = True
        return 7

    monkeypatch.setattr(cli_main.pytest, "main", fake_pytest_main)

    assert cli_main.main() == 7
    assert seen == {"called": True}


def test_gltest_dispatches_bench_subcommand(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["gltest", "bench", "contract.py", "--method", "ping"],
    )
    seen = {}

    def fake_bench_main(argv):
        seen["argv"] = argv
        return 0

    monkeypatch.setattr(bench_cli, "main", fake_bench_main)

    assert cli_main.main() == 0
    assert seen["argv"] == ["contract.py", "--method", "ping"]


def test_bench_json_output_and_arguments(monkeypatch, tmp_path, capsys):
    contract = tmp_path / "Contract.py"
    contract.write_text("# contract")
    seen = {}

    def fake_run(
        contract_path,
        method_name,
        constructor_args,
        method_args,
        iterations,
        warmup_iterations,
    ):
        seen.update(
            contract_path=contract_path,
            method_name=method_name,
            constructor_args=constructor_args,
            method_args=method_args,
            iterations=iterations,
            warmup_iterations=warmup_iterations,
        )
        return _result()

    monkeypatch.setattr(bench_cli, "_run_direct", fake_run)

    rc = bench_cli.main(
        [
            str(contract),
            "--method",
            "ping",
            "--iterations",
            "2",
            "--warmup",
            "1",
            "--constructor-args",
            "[1]",
            "--args",
            "[\"hello\"]",
            "--json",
            "--include-samples",
        ]
    )

    assert rc == 0
    assert seen == {
        "contract_path": contract,
        "method_name": "ping",
        "constructor_args": [1],
        "method_args": ["hello"],
        "iterations": 2,
        "warmup_iterations": 1,
    }
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["p95_ms"] == 3.0
    assert payload["samples_ms"] == [1.0, 3.0]


def test_json_mode_redirects_contract_stdout_to_stderr(monkeypatch, tmp_path, capsys):
    contract = tmp_path / "Contract.py"
    contract.write_text("# contract")

    def fake_run(*_args):
        print("contract noise")
        return _result()

    monkeypatch.setattr(bench_cli, "_run_direct", fake_run)

    assert (
        bench_cli.main(
            [
                str(contract),
                "--method",
                "ping",
                "--json",
            ]
        )
        == 0
    )

    captured = capsys.readouterr()
    json.loads(captured.out)
    assert "contract noise" not in captured.out
    assert "contract noise" in captured.err


@pytest.mark.parametrize(
    ("option", "value", "message"),
    [
        ("--args", "{", "--args must be valid JSON"),
        ("--constructor-args", "{}", "--constructor-args must be a JSON array"),
    ],
)
def test_invalid_json_args_report_cli_usage_error(
    monkeypatch,
    tmp_path,
    capsys,
    option,
    value,
    message,
):
    contract = tmp_path / "Contract.py"
    contract.write_text("# contract")
    monkeypatch.setattr(bench_cli, "_run_direct", lambda *_args: _result())

    with pytest.raises(SystemExit) as exc:
        bench_cli.main(
            [
                str(contract),
                "--method",
                "ping",
                option,
                value,
            ]
        )

    assert exc.value.code == 2
    assert message in capsys.readouterr().err


def test_bench_selects_studio_adapter(monkeypatch, tmp_path):
    contract = tmp_path / "Contract.py"
    contract.write_text("# contract")
    seen = {}

    def fake_run(*args):
        seen["args"] = args
        return _result(mode="studio")

    monkeypatch.setattr(bench_cli, "_run_studio", fake_run)

    assert (
        bench_cli.main(
            [
                str(contract),
                "--method",
                "ping",
                "--mode",
                "studio",
                "--iterations",
                "2",
            ]
        )
        == 0
    )
    assert seen["args"][1] == "ping"


def test_studio_write_benchmark_rejects_failed_receipts(monkeypatch):
    import gltest
    import gltest.assertions as assertions

    class FakeContractFunction:
        read_only = False

        def transact(self):
            return {"status": "failed"}

    class FakeContract:
        def ping(self, args=None):
            return FakeContractFunction()

    class FakeFactory:
        def deploy(self, args=None):
            return FakeContract()

    monkeypatch.setattr(
        gltest,
        "get_contract_factory",
        lambda contract_file_path: FakeFactory(),
    )
    monkeypatch.setattr(assertions, "tx_execution_succeeded", lambda _receipt: False)

    with pytest.raises(RuntimeError, match="Studio benchmark transaction failed"):
        bench_cli._run_studio(
            contract_path=None,
            method_name="ping",
            constructor_args=[],
            method_args=[],
            iterations=1,
            warmup_iterations=0,
        )


def test_human_output_handles_unavailable_throughput():
    output = bench_cli._format_human(_result(throughput=None))
    assert "Throughput: n/a" in output
