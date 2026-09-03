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


@pytest.mark.parametrize(
    ("branch", "version", "message"),
    [
        ("main", "0.30.0", "not a release branch"),
        ("v0.29-dev", "0.30.0-rc.1", "belongs to v0.30"),
        ("v0.30", "0.30.0-rc.1", "must be cut from v0.30-dev"),
        ("v0.30-dev", "0.30.0", "must be cut from v0.30"),
    ],
)
def test_release_version_rejects_wrong_release_route(branch, version, message):
    with pytest.raises(ValueError, match=message):
        release_version.validate_branch_version(branch, version)


def test_release_version_accepts_rc_only_on_owning_dev_line():
    version = release_version.validate_branch_version("v0.30-dev", "0.30.0rc1")

    assert version.normalized == "0.30.0-rc.1"


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


def test_semantic_release_routes_stable_and_rc_branches():
    config_path = Path(__file__).parents[1] / "releaserc.toml"
    branch_config = tomllib.loads(config_path.read_text())["semantic_release"][
        "branches"
    ]

    assert branch_config == {
        "stable": {
            "match": r"^v[0-9]+\.[0-9]+$",
            "prerelease_token": "rc",
            "prerelease": False,
        },
        "dev": {
            "match": r"^v[0-9]+\.[0-9]+-dev$",
            "prerelease_token": "rc",
            "prerelease": True,
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
