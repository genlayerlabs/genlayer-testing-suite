from gltest import get_contract_factory


def test_stats_functionality():
    """Test the stats functionality returns MethodStatsSummary object."""

    factory = get_contract_factory("Storage")
    contract = factory.deploy(args=["initial"], wait_retries=40)

    # Test stats method
    stats = contract.update_storage(args=["new_value"]).stats(
        provider="openai", model="gpt-4o", runs=3
    )

    # Verify it's a MethodStatsSummary object
    assert hasattr(stats, "method")
    assert hasattr(stats, "args")
    assert hasattr(stats, "total_runs")
    assert hasattr(stats, "execution_time")
    assert hasattr(stats, "provider")
    assert hasattr(stats, "model")

    # Check basic properties
    assert stats.method == "update_storage"
    assert stats.args == ["new_value"]
    assert stats.total_runs == 3
    assert stats.provider == "openai"
    assert stats.model == "gpt-4o"
    assert isinstance(stats.execution_time, float)

    # Check string representation
    stats_str = str(stats)
    assert "Method stats summary" in stats_str
    assert "Method: update_storage" in stats_str
    assert "Args: ['new_value']" in stats_str
    assert "Total runs: 3" in stats_str
    assert "Provider: openai" in stats_str
    assert "Model: gpt-4o" in stats_str
