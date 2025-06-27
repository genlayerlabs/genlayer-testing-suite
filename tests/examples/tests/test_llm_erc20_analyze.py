from gltest import get_contract_factory, get_default_account, create_account


TOKEN_TOTAL_SUPPLY = 1000
TRANSFER_AMOUNT = 100


def test_llm_erc20_analyze(setup_validators):
    setup_validators()
    # Account Setup
    from_account_a = get_default_account()
    from_account_b = create_account()

    # Deploy Contract
    factory = get_contract_factory("LlmErc20")
    contract = factory.deploy(args=[TOKEN_TOTAL_SUPPLY])

    # Get Initial State
    contract_state_1 = contract.get_balances(args=[]).call()
    assert contract_state_1[from_account_a.address] == TOKEN_TOTAL_SUPPLY

    # Transfer from User A to User B
    stats = contract.transfer(args=[TRANSFER_AMOUNT, from_account_b.address]).analyze(
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
    assert stats.method == "transfer"
    assert stats.args == [TRANSFER_AMOUNT, from_account_b.address]
    assert stats.total_runs == 3
    assert stats.provider == "openai"
    assert stats.model == "gpt-4o"
    assert isinstance(stats.execution_time, float)

    # Check string representation
    stats_str = str(stats)
    assert "Method analysis summary" in stats_str
    assert "Method: transfer" in stats_str
    assert f"Args: [{TRANSFER_AMOUNT}, '{from_account_b.address}']" in stats_str
    assert f"Total runs: {stats.total_runs}" in stats_str
    assert f"Provider: {stats.provider}" in stats_str
    assert f"Model: {stats.model}" in stats_str
