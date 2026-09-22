import pytest

from src.wallet import Wallet, InsufficientFundsError, play_session

def test_balance_updates_correctly_after_win_and_loss():
    """A win credits winnings; a loss simply keeps the stake gone."""
    w = Wallet(balance=100)
    w.place_bet(10)              # balance -> 90
    w.credit(10 * 5)            # a 5x win -> +50 -> 140
    assert w.balance == 140

def test_player_cannot_bet_more_than_balance():
    """A player must never be able to stake money they don't have."""
    w = Wallet(balance=5)
    with pytest.raises(InsufficientFundsError):
        w.place_bet(10)
    assert w.balance == 5        # balance untouched after a rejected bet

def test_gamblers_ruin_over_long_session():
    """
    Games & gamers insight: with a house edge (RTP < 100%), a player with a
    finite bankroll who keeps playing will almost always end up broke.
    Over a long session, the vast majority of seeds should end in ruin.
    """
    ruin_count = 0
    trials = 200
    for seed in range(trials):
        result = play_session(starting_balance=100, bet=1,
                              max_spins=100_000, seed=seed)
        if result["went_broke"]:
            ruin_count += 1
    # With a ~55% RTP game, essentially every long session ends in ruin.
    assert ruin_count / trials > 0.95

def test_short_session_can_end_in_profit():
    """
    Equally important: in the SHORT term, variance means a lucky player CAN
    walk away ahead. A game where nobody ever wins short-term would be broken
    (and would feel awful to players).
    """
    saw_profit = any(
        play_session(100, bet=1, max_spins=50, seed=s)["final_balance"] > 100
        for s in range(100)
    )
    assert saw_profit

def test_session_stops_when_balance_depleted():
    """The session must halt cleanly once the player can't afford a spin."""
    result = play_session(starting_balance=10, bet=1,
                         max_spins=1_000_000, seed=1)
    assert result["spins_played"] <= 1_000_000
    assert result["final_balance"] < 1     # can't afford the min bet anymore