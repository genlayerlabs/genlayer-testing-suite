# genlayer-testing-suite

## Releases

This repo uses a branch-per-major release model. There is no `main`. Releases are deliberate, not automatic.

See `.claude/skills/release/SKILL.md` for the full release flow. Short version:

- Branches are per-major: `v0.29` (current stable), `v<next>-dev` when next-major work is in progress.
- Releases go through `scripts/release.sh` on the target branch. The script bumps `pyproject.toml` + `glsim/__init__.py`, updates `CHANGELOG.md` via python-semantic-release, commits, tags `vX.Y.Z`, and pushes.
- `publish.yml` fires on the tag push and ships to PyPI.
- **Semver-zero rule**: this package is on 0.x, so minor IS the breaking-change boundary. `0.29 → 0.30` is a major bump and needs a new branch — `scripts/release.sh` refuses `minor`/`major` keywords without `--allow-major`.

**When user says "release":**
- Invoke the release skill. It will confirm version + branch, run pre-flight checks, then call `scripts/release.sh`.
- If CI on the tag fails, inspect the workflow logs (`gh run view`) — fix the issue, delete the bad tag, re-run the script.

## Architecture

- `gltest/direct/` — native Python test runner (no WASM/simulator)
- `glsim/` — lightweight GenLayer simulator (FastAPI JSON-RPC server)
- `gltest_cli/` — CLI and pytest plugin config
- Tests: `tests/` (152+ tests)

## Conventional Commits

Commits should still use conventional format because the release script generates the changelog from them:
- `feat(scope): description` — new feature
- `fix(scope): description` — bug fix
- `chore/docs/refactor/test: description` — no changelog entry
