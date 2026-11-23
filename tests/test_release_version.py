import importlib.util
from pathlib import Path
import sys
import tomllib

import pytest
import yaml


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "release_version.py"
SPEC = importlib.util.spec_from_file_location("release_version", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
release_version = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = release_version
SPEC.loader.exec_module(release_version)


@pytest.mark.parametrize(
    ("raw", "normalized", "branch", "is_prerelease"),
    [
        ("0.30.0", "0.30.0", "v0.30", False),
        ("v0.30.0-rc.1", "0.30.0-rc.1", "v0.30-dev", True),
        ("0.30.0rc2", "0.30.0-rc.2", "v0.30-dev", True),
    ],
)
def test_release_version_normalizes_pep440_rc_spellings(
    raw, normalized, branch, is_prerelease
):
    version = release_version.parse_release_version(raw)

    assert version.normalized == normalized
    assert version.release_branch == branch
    assert version.is_prerelease is is_prerelease


@pytest.mark.parametrize("raw", ["0.30.1", "0.30.1-rc.2"])
def test_release_version_names_the_dev_and_stable_branch_of_its_line(raw):
    version = release_version.parse_release_version(raw)

    assert version.dev_branch == "v0.30-dev"
    assert version.stable_branch == "v0.30"


@pytest.mark.parametrize(
    ("branch", "version", "message"),
    [
        ("main", "0.30.0", "not a release branch"),
        ("v0.29-dev", "0.30.0-rc.1", "belongs to v0.30"),
        ("v0.29-dev", "0.30.0", "belongs to v0.30"),
        ("v0.30", "0.30.0-rc.1", "must be cut from v0.30-dev"),
        ("v0.30", "0.30.0", "must be cut from v0.30-dev"),
    ],
)
def test_release_version_rejects_wrong_release_route(branch, version, message):
    with pytest.raises(ValueError, match=message):
        release_version.validate_branch_version(branch, version)


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [("0.30.0rc1", "0.30.0-rc.1"), ("0.30.0", "0.30.0"), ("v0.30.1", "0.30.1")],
)
def test_release_version_accepts_rcs_and_finals_on_owning_dev_line(raw, normalized):
    version = release_version.validate_branch_version("v0.30-dev", raw)

    assert version.normalized == normalized


@pytest.mark.parametrize(
    ("conclusions", "verdict"),
    [
        ([], "missing"),
        (["cancelled", "skipped"], "missing"),
        (["success"], "green"),
        (["success", "cancelled"], "green"),
        (["success", "failure"], "red"),
        (["timed_out"], "red"),
    ],
)
def test_runs_verdict_needs_a_green_run_and_no_red_one(conclusions, verdict):
    assert release_version.runs_verdict(conclusions) == verdict


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["dev-branch", "0.30.1"], "v0.30-dev"),
        (["stable-branch", "0.30.1"], "v0.30"),
        (["branch", "0.30.1"], "v0.30"),
        (["branch", "0.30.1-rc.1"], "v0.30-dev"),
        (["runs-verdict"], "missing"),
        (["runs-verdict", "success", "success"], "green"),
    ],
)
def test_release_version_cli_prints_branches_and_verdicts(argv, expected, capsys):
    assert release_version.main(["release_version.py", *argv]) == 0
    assert capsys.readouterr().out.strip() == expected


@pytest.mark.parametrize("version", ["0.30.0-alpha.1", "0.30.0-rc.0", "00.30.0"])
def test_release_version_rejects_non_rc_or_noncanonical_versions(version):
    with pytest.raises(ValueError, match="not a supported release version"):
        release_version.parse_release_version(version)


def test_release_tag_and_package_version_compare_after_normalization():
    assert (
        release_version.main(
            ["release_version.py", "verify-tag", "v0.30.0-rc.1", "0.30.0rc1"]
        )
        == 0
    )


@pytest.mark.parametrize(
    ("version", "existing"),
    [
        ("0.19.1", ["0.19.0"]),
        ("0.19.1", ["0.19.1-rc.2", "0.19.0"]),
        ("0.19.1-rc.2", ["0.19.1-rc.1"]),
        ("0.19.1-rc.1", []),
    ],
)
def test_release_version_accepts_a_version_newer_than_the_existing_ones(
    version, existing
):
    assert release_version.assert_newer(version, existing).normalized == version


@pytest.mark.parametrize(
    ("version", "existing", "blocker"),
    [
        ("0.19.1-rc.1", ["0.19.1"], "0.19.1"),
        ("0.19.1", ["0.19.0", "0.19.1"], "0.19.1"),
        ("0.19.0-rc.9", ["0.19.0"], "0.19.0"),
        ("0.19.1-rc.1", ["0.19.1-rc.2"], "0.19.1-rc.2"),
    ],
)
def test_release_version_refuses_a_version_that_does_not_move_forward(
    version, existing, blocker
):
    with pytest.raises(ValueError, match=f"not newer than {blocker}"):
        release_version.assert_newer(version, existing)


def test_runs_verdict_reports_a_run_that_is_still_in_progress():
    assert release_version.runs_verdict(["success", "pending"]) == "pending"
    assert release_version.runs_verdict(["pending", "failure"]) == "red"


def test_release_version_cli_checks_that_a_version_moves_forward(capsys):
    assert release_version.main(["release_version.py", "assert-newer", "0.19.1", "0.19.0"]) == 0
    assert capsys.readouterr().out.strip() == "0.19.1"
    assert release_version.main(["release_version.py", "assert-newer", "0.19.1-rc.1", "0.19.1"]) == 2
    assert "not newer than 0.19.1" in capsys.readouterr().err


def test_semantic_release_only_releases_from_dev_branches():
    config_path = Path(__file__).parents[1] / "releaserc.toml"
    branch_config = tomllib.loads(config_path.read_text())["semantic_release"][
        "branches"
    ]

    # release.sh adds --as-prerelease for RCs, so the group itself stays final.
    assert branch_config == {
        "dev": {
            "match": r"^v[0-9]+\.[0-9]+-dev$",
            "prerelease_token": "rc",
            "prerelease": False,
        },
    }


def test_publish_workflow_is_tag_only_and_enforces_release_provenance():
    workflow_path = Path(__file__).parents[1] / ".github" / "workflows" / "publish.yml"
    workflow = yaml.load(workflow_path.read_text(), Loader=yaml.BaseLoader)

    assert workflow["on"] == {"push": {"tags": ["v*.*.*"]}}
    assert workflow["permissions"] == {"contents": "write"}

    publish_steps = workflow["jobs"]["publish-to-pypi"]["steps"]
    verification = next(
        step["run"]
        for step in publish_steps
        if step["name"] == "Verify tag, package version, and owning branch"
    )
    assert "release_version.py verify-tag" in verification
    assert "release_version.py branch" in verification
    assert 'TAG_COMMIT" != "$BRANCH_HEAD' in verification

    github_release = next(
        step["run"] for step in publish_steps if step["name"] == "Create GitHub Release"
    )
    assert "release_version.py is-prerelease" in github_release
    assert "--prerelease" in github_release
