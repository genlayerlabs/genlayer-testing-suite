import sys

import pytest


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "bench":
        from gltest_cli.bench import main as bench_main

        return bench_main(sys.argv[2:])
    return pytest.main()
