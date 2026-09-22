import math
import pytest
from src.slot_engine import SlotConfig, payout_for_reels, spin_payout
from src.wallet import Wallet, InvalidBetError, play_session_with_loss_limit
from src.rng_audit import chi_square_fairness


@pytest.mark.parametrize("symbol,multiple", list(zip(SlotConfig().symbols, SlotConfig().payouts)))
def test_each_payout(symbol, multiple):
    assert payout_for_reels((symbol,) * 3) == multiple


def test_mixed_reels_and_injected_stops():
    assert payout_for_reels(("Seven", "Bar", "Seven")) == 0
    class Stops:
        def __init__(self):
            self.stops = iter((0, 6, 0))
        def randrange(self, length):
            return next(self.stops)
    assert spin_payout(Stops()) == 0


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1, True, "10", 1.5])
def test_invalid_credit_preserves_balance(bad):
    wallet = Wallet(100)
    with pytest.raises(InvalidBetError):
        wallet.credit(bad)
    assert wallet.balance == 100


@pytest.mark.parametrize("kwargs", [{"balance": float("nan")}, {"balance": -1},
                                     {"balance": 10, "min_bet": 20, "max_bet": 10}])
def test_invalid_wallet_configuration(kwargs):
    with pytest.raises(ValueError):
        Wallet(**kwargs)


def test_limit_rejects_stake_that_would_cross_boundary():
    result = play_session_with_loss_limit(100, 10, 15, 10, spin_fn=lambda rng, config: 0)
    assert result == {"final_balance": 90, "spins_played": 1, "stopped_by_limit": True}


def test_invalid_config_and_audit_counts():
    with pytest.raises(ValueError):
        SlotConfig(strip_counts=(0, 5, 4, 3, 2))
    with pytest.raises(ValueError):
        chi_square_fairness([1, 2, math.nan, 4, 5])
