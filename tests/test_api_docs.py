import importlib.util
import inspect
import re
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


def _sections(markdown):
    """Map '## Heading' -> section text."""
    parts = re.split(r"^## ", markdown, flags=re.MULTILINE)[1:]
    return {part.split("\n", 1)[0].strip(): part for part in parts}


def test_every_public_method_is_documented_under_its_class(tmp_path):
    from gltest.contracts.contract_factory import ContractFactory
    from gltest.contracts.contract_functions import ContractFunction
    from gltest.direct import VMContext
    from gltest.validators import Validator, ValidatorFactory

    generate_api_docs.main([str(tmp_path)])
    pages = {
        "integration.md": _sections((tmp_path / "integration.md").read_text()),
        "direct.md": _sections((tmp_path / "direct.md").read_text()),
    }
    skipped = {"from_name", "from_file_path", "get_create2_raw", "get_message_raw"}
    expected_layout = (
        (ContractFactory, "integration.md", "factory."),
        (ContractFunction, "integration.md", "contract.method_name."),
        (ValidatorFactory, "integration.md", "validator_factory."),
        (Validator, "integration.md", "validator."),
        (VMContext, "direct.md", "vm."),
    )
    for cls, page, prefix in expected_layout:
        # Independent of generate_api_docs.public_methods: use inspect directly.
        expected = {
            name
            for name, value in inspect.getmembers(cls)
            if not name.startswith("_") and callable(value)
        } - skipped
        assert expected
        section = pages[page][cls.__name__]
        for name in expected:
            assert f"### `{prefix}{name}`" in section, (
                f"{cls.__name__}.{name} missing from the {cls.__name__} section of {page}"
            )


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


def test_type_normalization_keeps_literal_contents():
    from typing import Literal, Optional

    assert (
        generate_api_docs.format_type(Optional[Literal["profile.Production"]])
        == "Optional[Literal['profile.Production']]"
    )


def test_type_normalization_keeps_quote_paren_and_escapes():
    from typing import ForwardRef, Literal, Optional

    fmt = generate_api_docs.format_type
    assert fmt(Literal["closing')"]) == "Literal[\"closing')\"]"
    assert fmt(Literal["it's"]) == "Literal[\"it's\"]"
    assert fmt(Literal["a.B"]) == "Literal['a.B']"
    assert fmt(Optional[ForwardRef("Foo")]) == "Optional[Foo]"
