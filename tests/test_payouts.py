"""Tests for the game configuration and payout accounting."""

import numpy as np
import pytest

from src.slot_engine import DEFAULT_CONFIG, simulate, symbol_probabilities

def test_strip_counts_sum_to_reel_length():
    """The strip must contain exactly the declared number of symbols."""
    assert sum(DEFAULT_CONFIG.strip_counts) == DEFAULT_CONFIG.reel_length == 20

def test_config_lists_have_equal_length():
    """symbols, strip_counts and payouts must stay aligned."""
    assert (
        len(DEFAULT_CONFIG.symbols)
        == len(DEFAULT_CONFIG.strip_counts)
        == len(DEFAULT_CONFIG.payouts)
    )

def test_probabilities_sum_to_one():
    """Symbol probabilities must form a valid distribution."""
    assert symbol_probabilities().sum() == pytest.approx(1.0, abs=1e-12)

def test_total_bet_accounting_is_correct():
    """Total bet must equal n_spins * bet — no money can be lost in accounting."""
    n = 10_000
    result = simulate(n_spins=n, seed=99)
    assert result["total_bet"] == n * DEFAULT_CONFIG.bet

def test_winnings_are_never_negative():
    """A player can never win a negative amount."""
    result = simulate(n_spins=10_000, seed=99)
    assert result["total_win"] >= 0

def test_symbol_counts_total_matches_reels_drawn():
    """Every reel position must be accounted for (n_spins * 3 symbols)."""
    n = 10_000
    result = simulate(n_spins=n, seed=99)
    assert int(np.sum(result["symbol_counts"])) == n * 3