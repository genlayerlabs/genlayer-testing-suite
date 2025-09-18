from unittest.mock import patch
from gltest.decorators import (
    gl_only_on_chains,
    gl_skip_on_chains,
    gl_only_localnet,
    gl_only_studionet,
    gl_only_testnet_asimov,
    gl_skip_localnet,
    gl_skip_studionet,
    gl_skip_testnet_asimov,
)
from gltest.types import ChainType


class TestGlOnlyOnChains:
    """Test gl_only_on_chains decorator."""

    def test_skips_when_chain_not_in_list(self):
        """Test that function is skipped when current chain is not in the allowed list."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            mock_config.return_value.get_chain_type.return_value = "testnet_asimov"

            @gl_only_on_chains([ChainType.LOCALNET, ChainType.STUDIONET])
            def test_func():
                return "executed"

            # Check that pytest.mark.skipif was applied
            assert hasattr(test_func, "pytestmark")
            marks = (
                test_func.pytestmark
                if isinstance(test_func.pytestmark, list)
                else [test_func.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert len(skip_marks) > 0

            # Verify skip condition is True
            skip_mark = skip_marks[0]
            assert skip_mark.args[0] is True  # Should skip
            assert (
                "Test only runs on: localnet, studionet" in skip_mark.kwargs["reason"]
            )

    def test_does_not_skip_when_chain_in_list(self):
        """Test that function runs when current chain is in the allowed list."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            mock_config.return_value.get_chain_type.return_value = "localnet"

            @gl_only_on_chains([ChainType.LOCALNET, ChainType.STUDIONET])
            def test_func():
                return "executed"

            # Check that pytest.mark.skipif was applied with False condition
            assert hasattr(test_func, "pytestmark")
            marks = (
                test_func.pytestmark
                if isinstance(test_func.pytestmark, list)
                else [test_func.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert len(skip_marks) > 0

            skip_mark = skip_marks[0]
            assert skip_mark.args[0] is False  # Should not skip

    def test_accepts_string_chains(self):
        """Test that decorator accepts string chain names."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            mock_config.return_value.get_chain_type.return_value = "custom_chain"

            @gl_only_on_chains(["custom_chain", "another_chain"])
            def test_func():
                return "executed"

            marks = (
                test_func.pytestmark
                if isinstance(test_func.pytestmark, list)
                else [test_func.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            skip_mark = skip_marks[0]
            assert skip_mark.args[0] is False  # Should not skip on custom_chain

    def test_works_on_classes(self):
        """Test that decorator works on test classes."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            mock_config.return_value.get_chain_type.return_value = "testnet_asimov"

            @gl_only_on_chains([ChainType.LOCALNET])
            class TestClass:
                def test_method(self):
                    pass

            assert hasattr(TestClass, "pytestmark")
            marks = (
                TestClass.pytestmark
                if isinstance(TestClass.pytestmark, list)
                else [TestClass.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert len(skip_marks) > 0
            assert skip_marks[0].args[0] is True  # Should skip


class TestGlSkipOnChains:
    """Test gl_skip_on_chains decorator."""

    def test_skips_when_chain_in_list(self):
        """Test that function is skipped when current chain is in the skip list."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            mock_config.return_value.get_chain_type.return_value = "localnet"

            @gl_skip_on_chains([ChainType.LOCALNET, ChainType.STUDIONET])
            def test_func():
                return "executed"

            marks = (
                test_func.pytestmark
                if isinstance(test_func.pytestmark, list)
                else [test_func.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            skip_mark = skip_marks[0]
            assert skip_mark.args[0] is True  # Should skip
            assert "Test skipped on: localnet, studionet" in skip_mark.kwargs["reason"]

    def test_does_not_skip_when_chain_not_in_list(self):
        """Test that function runs when current chain is not in the skip list."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            mock_config.return_value.get_chain_type.return_value = "testnet_asimov"

            @gl_skip_on_chains([ChainType.LOCALNET, ChainType.STUDIONET])
            def test_func():
                return "executed"

            marks = (
                test_func.pytestmark
                if isinstance(test_func.pytestmark, list)
                else [test_func.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            skip_mark = skip_marks[0]
            assert skip_mark.args[0] is False  # Should not skip

    def test_accepts_string_chains(self):
        """Test that decorator accepts string chain names."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            mock_config.return_value.get_chain_type.return_value = "custom_chain"

            @gl_skip_on_chains(["custom_chain", "another_chain"])
            def test_func():
                return "executed"

            marks = (
                test_func.pytestmark
                if isinstance(test_func.pytestmark, list)
                else [test_func.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            skip_mark = skip_marks[0]
            assert skip_mark.args[0] is True  # Should skip on custom_chain

    def test_works_on_classes(self):
        """Test that decorator works on test classes."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            mock_config.return_value.get_chain_type.return_value = "localnet"

            @gl_skip_on_chains([ChainType.LOCALNET])
            class TestClass:
                def test_method(self):
                    pass

            assert hasattr(TestClass, "pytestmark")
            marks = (
                TestClass.pytestmark
                if isinstance(TestClass.pytestmark, list)
                else [TestClass.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert len(skip_marks) > 0
            assert skip_marks[0].args[0] is True  # Should skip


class TestConvenienceDecorators:
    """Test the convenience decorators for specific chains."""

    def test_gl_only_localnet(self):
        """Test gl_only_localnet decorator."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            # Should skip when not on localnet
            mock_config.return_value.get_chain_type.return_value = "testnet_asimov"

            @gl_only_localnet
            def test_func():
                return "executed"

            marks = (
                test_func.pytestmark
                if isinstance(test_func.pytestmark, list)
                else [test_func.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert skip_marks[0].args[0] is True  # Should skip

            # Should not skip when on localnet
            mock_config.return_value.get_chain_type.return_value = "localnet"

            @gl_only_localnet
            def test_func2():
                return "executed"

            marks = (
                test_func2.pytestmark
                if isinstance(test_func2.pytestmark, list)
                else [test_func2.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert skip_marks[0].args[0] is False  # Should not skip

    def test_gl_only_studionet(self):
        """Test gl_only_studionet decorator."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            # Should skip when not on studionet
            mock_config.return_value.get_chain_type.return_value = "localnet"

            @gl_only_studionet
            def test_func():
                return "executed"

            marks = (
                test_func.pytestmark
                if isinstance(test_func.pytestmark, list)
                else [test_func.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert skip_marks[0].args[0] is True  # Should skip

            # Should not skip when on studionet
            mock_config.return_value.get_chain_type.return_value = "studionet"

            @gl_only_studionet
            def test_func2():
                return "executed"

            marks = (
                test_func2.pytestmark
                if isinstance(test_func2.pytestmark, list)
                else [test_func2.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert skip_marks[0].args[0] is False  # Should not skip

    def test_gl_only_testnet_asimov(self):
        """Test gl_only_testnet_asimov decorator."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            # Should skip when not on testnet_asimov
            mock_config.return_value.get_chain_type.return_value = "localnet"

            @gl_only_testnet_asimov
            def test_func():
                return "executed"

            marks = (
                test_func.pytestmark
                if isinstance(test_func.pytestmark, list)
                else [test_func.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert skip_marks[0].args[0] is True  # Should skip

            # Should not skip when on testnet_asimov
            mock_config.return_value.get_chain_type.return_value = "testnet_asimov"

            @gl_only_testnet_asimov
            def test_func2():
                return "executed"

            marks = (
                test_func2.pytestmark
                if isinstance(test_func2.pytestmark, list)
                else [test_func2.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert skip_marks[0].args[0] is False  # Should not skip

    def test_gl_skip_localnet(self):
        """Test gl_skip_localnet decorator."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            # Should skip when on localnet
            mock_config.return_value.get_chain_type.return_value = "localnet"

            @gl_skip_localnet
            def test_func():
                return "executed"

            marks = (
                test_func.pytestmark
                if isinstance(test_func.pytestmark, list)
                else [test_func.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert skip_marks[0].args[0] is True  # Should skip

            # Should not skip when not on localnet
            mock_config.return_value.get_chain_type.return_value = "testnet_asimov"

            @gl_skip_localnet
            def test_func2():
                return "executed"

            marks = (
                test_func2.pytestmark
                if isinstance(test_func2.pytestmark, list)
                else [test_func2.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert skip_marks[0].args[0] is False  # Should not skip

    def test_gl_skip_studionet(self):
        """Test gl_skip_studionet decorator."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            # Should skip when on studionet
            mock_config.return_value.get_chain_type.return_value = "studionet"

            @gl_skip_studionet
            def test_func():
                return "executed"

            marks = (
                test_func.pytestmark
                if isinstance(test_func.pytestmark, list)
                else [test_func.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert skip_marks[0].args[0] is True  # Should skip

            # Should not skip when not on studionet
            mock_config.return_value.get_chain_type.return_value = "localnet"

            @gl_skip_studionet
            def test_func2():
                return "executed"

            marks = (
                test_func2.pytestmark
                if isinstance(test_func2.pytestmark, list)
                else [test_func2.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert skip_marks[0].args[0] is False  # Should not skip

    def test_gl_skip_testnet_asimov(self):
        """Test gl_skip_testnet_asimov decorator."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            # Should skip when on testnet_asimov
            mock_config.return_value.get_chain_type.return_value = "testnet_asimov"

            @gl_skip_testnet_asimov
            def test_func():
                return "executed"

            marks = (
                test_func.pytestmark
                if isinstance(test_func.pytestmark, list)
                else [test_func.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert skip_marks[0].args[0] is True  # Should skip

            # Should not skip when not on testnet_asimov
            mock_config.return_value.get_chain_type.return_value = "localnet"

            @gl_skip_testnet_asimov
            def test_func2():
                return "executed"

            marks = (
                test_func2.pytestmark
                if isinstance(test_func2.pytestmark, list)
                else [test_func2.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            assert skip_marks[0].args[0] is False  # Should not skip


class TestMixedChainTypes:
    """Test mixing ChainType enums and strings."""

    def test_mixed_chain_types_in_only(self):
        """Test that gl_only_on_chains handles mixed ChainType and string values."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            mock_config.return_value.get_chain_type.return_value = "localnet"

            @gl_only_on_chains([ChainType.LOCALNET, "custom_chain"])
            def test_func():
                return "executed"

            marks = (
                test_func.pytestmark
                if isinstance(test_func.pytestmark, list)
                else [test_func.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            skip_mark = skip_marks[0]
            assert skip_mark.args[0] is False  # Should not skip on localnet
            assert "localnet, custom_chain" in skip_mark.kwargs["reason"]

    def test_mixed_chain_types_in_skip(self):
        """Test that gl_skip_on_chains handles mixed ChainType and string values."""
        with patch("gltest.decorators.get_general_config") as mock_config:
            mock_config.return_value.get_chain_type.return_value = "localnet"

            @gl_skip_on_chains([ChainType.LOCALNET, "custom_chain"])
            def test_func():
                return "executed"

            marks = (
                test_func.pytestmark
                if isinstance(test_func.pytestmark, list)
                else [test_func.pytestmark]
            )
            skip_marks = [m for m in marks if m.name == "skipif"]
            skip_mark = skip_marks[0]
            assert skip_mark.args[0] is True  # Should skip on localnet
            assert "localnet, custom_chain" in skip_mark.kwargs["reason"]
