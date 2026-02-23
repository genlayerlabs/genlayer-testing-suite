"""CLI entry point for glsim."""

import argparse

from .state import DEFAULT_CHAIN_ID


def main():
    parser = argparse.ArgumentParser(
        prog="glsim",
        description="GenLayer Sim — lightweight local GenLayer network",
    )
    parser.add_argument(
        "--port", type=int, default=4000, help="RPC server port (default: 4000)"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--validators", type=int, default=5, help="Number of validators (default: 5)"
    )
    parser.add_argument(
        "--max-rotations", type=int, default=3,
        help="Max leader rotations on disagreement (default: 3)"
    )
    parser.add_argument(
        "--chain-id",
        type=int,
        default=DEFAULT_CHAIN_ID,
        help=f"Network/chain id reported by RPC (default: {DEFAULT_CHAIN_ID})",
    )
    parser.add_argument(
        "--llm-provider", default=None,
        help="Default LLM provider in format provider:model (e.g. openai:gpt-4o)"
    )
    parser.add_argument(
        "--no-browser", action="store_true",
        help="Disable Playwright browser for web requests (use httpx only)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose logging"
    )
    parser.add_argument(
        "--seed", default=None,
        help="Deterministic seed for address generation. Random if omitted."
    )

    args = parser.parse_args()

    from .server import create_app, run_server

    app = create_app(
        num_validators=args.validators,
        max_rotations=args.max_rotations,
        chain_id=args.chain_id,
        llm_provider=args.llm_provider,
        use_browser=not args.no_browser,
        verbose=args.verbose,
        seed=args.seed,
    )
    run_server(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
