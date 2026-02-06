"""CLI entry point for glsim."""

import argparse


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
        "--validators", type=int, default=1, help="Number of validators (default: 1, leader-only)"
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

    args = parser.parse_args()

    from .server import create_app, run_server

    app = create_app(
        num_validators=args.validators,
        llm_provider=args.llm_provider,
        use_browser=not args.no_browser,
        verbose=args.verbose,
    )
    run_server(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
