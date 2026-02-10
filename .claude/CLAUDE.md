# genlayer-testing-suite

## Releases — CRITICAL

This repo uses `python-semantic-release` (config: `releaserc.toml`, CI: `.github/workflows/publish.yml`).

**NEVER do any of the following:**
- Manually edit version strings in `pyproject.toml` or `glsim/__init__.py`
- Manually create git tags (`git tag vX.Y.Z`)
- Manually run `semantic-release` locally
- Commit messages like `chore: bump version to X.Y.Z`

**How releases work:**
1. Push conventional commits to `main` (`feat:` → minor, `fix:` → patch)
2. CI runs `semantic-release version` which auto-bumps versions, creates commit + tag, pushes
3. CI builds and publishes to PyPI via twine

**When user says "release":**
- Verify all changes are committed and pushed to `main` with proper conventional commit prefixes
- That's it. CI handles the rest. Do NOT touch versions or tags.
- If CI fails, inspect the workflow logs (`gh run view`) — don't try to manually publish

**Version files managed by semantic-release:**
- `pyproject.toml:project.version`
- `glsim/__init__.py:__version__`

## Architecture

- `gltest/direct/` — native Python test runner (no WASM/simulator)
- `glsim/` — lightweight GenLayer simulator (FastAPI JSON-RPC server)
- `gltest_cli/` — CLI and pytest plugin config
- Tests: `tests/` (152+ tests)

## Conventional Commits

All commits must use conventional format:
- `feat(scope): description` — new feature (minor bump)
- `fix(scope): description` — bug fix (patch bump)
- `chore/docs/refactor/test: description` — no version bump
