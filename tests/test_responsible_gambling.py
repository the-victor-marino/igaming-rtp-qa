from src.wallet import play_session_with_loss_limit

def test_loss_limit_halts_play():
    """A player who hits their self-imposed loss limit must be stopped."""
    result = play_session_with_loss_limit(
        starting_balance=1000, bet=10, loss_limit=100,
        max_spins=1_000_000, seed=7,
    )
    net_loss = 1000 - result["final_balance"]
    assert result["stopped_by_limit"] is True
    # The limit should never be blown through by more than a single stake.
    assert net_loss <= 100 + 10

def test_loss_limit_never_exceeded_across_many_players():
    """The protection must hold for every seed, not just a lucky one."""
    for seed in range(100):
        result = play_session_with_loss_limit(
            starting_balance=1000, bet=10, loss_limit=200,
            max_spins=1_000_000, seed=seed,
        )
        assert (1000 - result["final_balance"]) <= 200 + 10