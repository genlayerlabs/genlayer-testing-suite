"""
GenLayer Sim (glsim) — Lightweight local GenLayer network.

A single-process Python server that speaks the same JSON-RPC protocol
as GenLayer Studio but executes contracts via the direct mode engine.
Supports real LLM and web calls without Docker or WASM.

    pip install genlayer-test[sim]
    glsim --port 4000
"""

__version__ = "0.20.1"
