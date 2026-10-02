# Benchmarking Intelligent Contracts

`gltest bench` measures repeated contract-method execution without replacing the
existing pytest-based `gltest` command.

## Direct mode

Use direct mode for fast local execution:

```bash
gltest bench contracts/Storage.py \
  --method get_storage \
  --mode direct \
  --iterations 100 \
  --warmup 5
```

Constructor and method arguments are JSON arrays:

```bash
gltest bench contracts/Counter.py \
  --method increment \
  --constructor-args '[0]' \
  --args '[2]'
```

## Studio mode

Use studio mode to measure the configured Studio/RPC execution path:

```bash
gltest bench contracts/Oracle.py \
  --method resolve \
  --mode studio \
  --iterations 20
```

The contract is deployed once before measurement. A read-only method is executed
with `.call()`; a state-changing method is executed with `.transact()`. Studio
latency therefore includes the configured RPC and transaction wait path. Direct
mode measures native local execution.

## Metrics

The report contains:

- mean, median, p95, minimum, and maximum wall-clock latency;
- total measured time and throughput in operations per second;
- process CPU time consumed during the measured loop;
- peak process RSS sampled after each measured execution.

Warmup executions and contract deployment are excluded from measured latency.
State-changing methods are not reset between iterations, so benchmarks that need
identical state should use an idempotent method or prepare a contract specifically
for benchmarking.

For machine-readable output:

```bash
gltest bench contracts/Storage.py --method get_storage --json
```

Add `--include-samples` to include each latency sample in the JSON result.
