"""
slot_engine.py
--------------
Core logic for a simple 3-reel slot machine, used as the "system under test"
for an iGaming QA portfolio project.

The module exposes small, single-purpose, deterministic functions so that a
pytest suite can assert on their return values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

@dataclass(frozen=True)
class SlotConfig:
    """Immutable configuration describing the slot game.

    All three reels are identical and share the same 20-symbol strip.
    A win only occurs on a three-of-a-kind across the single centre payline.
    """
    symbols: tuple[str, ...] = ("Cherry", "Lemon", "Bell", "Bar", "Seven")
    strip_counts: tuple[int, ...] = (6, 5, 4, 3, 2)   # sums to 20
    payouts: tuple[int, ...] = (5, 10, 15, 25, 50)    # multiplier per 3-of-a-kind
    bet: int = 1

    @property
    def reel_length(self) -> int:
        return sum(self.strip_counts)

    def __post_init__(self) -> None:
        # Basic integrity checks so a broken config fails fast.
        assert len(self.symbols) == len(self.strip_counts) == len(self.payouts), \
            "symbols, strip_counts and payouts must be the same length"
        assert all(c > 0 for c in self.strip_counts), "strip counts must be positive"

# A single shared default configuration used across the project.
DEFAULT_CONFIG = SlotConfig()

def symbol_probabilities(config: SlotConfig = DEFAULT_CONFIG) -> np.ndarray:
    """Probability of each symbol appearing on a single reel."""
    counts = np.asarray(config.strip_counts, dtype=float)
    return counts / config.reel_length

def theoretical_rtp(config: SlotConfig = DEFAULT_CONFIG) -> float:
    """Return the exact, analytically derived RTP (as a fraction, e.g. 0.545625).

    Reels are independent, so P(three-of-a-kind of symbol i) = p_i ** 3.
    RTP = sum_i ( p_i**3 * payout_i ) / bet
    """
    probs = symbol_probabilities(config)
    payouts = np.asarray(config.payouts, dtype=float)
    expected_return = np.sum((probs ** 3) * payouts)
    return float(expected_return / config.bet)

def simulate(
    n_spins: int,
    config: SlotConfig = DEFAULT_CONFIG,
    seed: int | None = None,
) -> dict:
    """Run a Monte Carlo simulation of `n_spins` spins.

    Parameters
    ----------
    n_spins : int
        Number of spins to simulate.
    config : SlotConfig
        Game configuration.
    seed : int | None
        Seed for the random number generator. Pass an int for reproducible
        (test-friendly) runs; pass None for a fresh random run.

    Returns
    -------
    dict with keys:
        'simulated_rtp'   : float  – final cumulative RTP (fraction)
        'cumulative_rtp'  : np.ndarray – cumulative RTP after each spin
        'symbol_counts'   : np.ndarray – observed count of each symbol across all reels
        'total_win'       : float  – total credits won
        'total_bet'       : float  – total credits wagered
    """
    if n_spins <= 0:
        raise ValueError("n_spins must be a positive integer")

    rng = np.random.default_rng(seed)
    probs = symbol_probabilities(config)
    payouts = np.asarray(config.payouts, dtype=float)
    n_symbols = len(config.symbols)

    # Draw the three reels for every spin at once (vectorised = fast).
    reels = rng.choice(n_symbols, size=(n_spins, 3), p=probs)

    # A win requires all three reels to match.
    is_win = (reels[:, 0] == reels[:, 1]) & (reels[:, 1] == reels[:, 2])

    win_amounts = np.zeros(n_spins, dtype=float)
    win_amounts[is_win] = payouts[reels[is_win, 0]]

    cumulative_win = np.cumsum(win_amounts)
    cumulative_bet = np.arange(1, n_spins + 1) * config.bet
    cumulative_rtp = cumulative_win / cumulative_bet

    symbol_counts = np.bincount(reels.ravel(), minlength=n_symbols)

    return {
        "simulated_rtp": float(cumulative_rtp[-1]),
        "cumulative_rtp": cumulative_rtp,
        "symbol_counts": symbol_counts,
        "total_win": float(cumulative_win[-1]),
        "total_bet": float(cumulative_bet[-1]),
    }