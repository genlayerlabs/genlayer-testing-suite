import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "generate_api_docs", ROOT / "scripts" / "generate-api-docs.py"
)
generate_api_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generate_api_docs)


def test_committed_api_docs_match_generator(tmp_path):
    """docs/api-references is generated; regenerate it with scripts/generate-api-docs.py."""
    generate_api_docs.main([str(tmp_path)])
    for generated in sorted(tmp_path.glob("*.md")):
        committed = ROOT / "docs" / "api-references" / generated.name
        assert committed.read_text() == generated.read_text(), (
            f"{committed} is stale: run `python scripts/generate-api-docs.py`"
        )


def test_every_public_method_is_documented(tmp_path):
    from gltest.contracts.contract_factory import ContractFactory
    from gltest.direct import VMContext

    generate_api_docs.main([str(tmp_path)])
    text = (tmp_path / "integration.md").read_text() + (
        tmp_path / "direct.md"
    ).read_text()
    skipped = {"from_name", "from_file_path", "get_create2_raw", "get_message_raw"}
    for cls in (ContractFactory, VMContext):
        for name in generate_api_docs.public_methods(cls):
            if name not in skipped:
                assert f".{name}`" in text


def test_defaults_and_types_are_deterministic():
    assert generate_api_docs.format_default(object()) == "<sentinel>"
    assert generate_api_docs.format_type(__import__("typing").Optional[str]) == "Optional[str]"


def test_parameter_kinds_are_preserved():
    def sample(a, /, b, *args, c=1, **kwargs):
        pass

    doc = generate_api_docs.generate_method_doc("sample", sample)
    assert "sample(a, /, b, *args, c = 1, **kwargs)" in doc.replace("c=1", "c = 1")
    assert "| `*args` | variadic positional |" in doc
    assert "| `**kwargs` | variadic keyword |  | No |" in doc
    assert "| `c` | keyword-only |  | No | `1` |" in doc

    def kw_only(a, *, b):
        pass

    assert "kw_only(a, *, b)" in generate_api_docs.generate_method_doc("kw_only", kw_only)
