"""Tests for RTP correctness and Monte Carlo convergence."""

import pytest

from src.slot_engine import theoretical_rtp, simulate

# The known, hand-verified RTP for the default configuration.
KNOWN_RTP = 0.545625

def test_theoretical_rtp_matches_known_value():
    """The analytic RTP must equal the hand-calculated value."""
    assert theoretical_rtp() == pytest.approx(KNOWN_RTP, abs=1e-9)

def test_theoretical_rtp_below_100_percent():
    """A valid casino game must always retain a house edge (RTP < 100%)."""
    assert theoretical_rtp() < 1.0

def test_simulated_rtp_converges_to_theoretical():
    """Over 500k seeded spins, simulated RTP must be within 1% of theory."""
    result = simulate(n_spins=500_000, seed=42)
    assert result["simulated_rtp"] == pytest.approx(theoretical_rtp(), abs=0.01)

def test_simulation_is_reproducible():
    """Same seed => identical result (a core QA requirement)."""
    a = simulate(n_spins=50_000, seed=7)
    b = simulate(n_spins=50_000, seed=7)
    assert a["simulated_rtp"] == b["simulated_rtp"]
    assert a["total_win"] == b["total_win"]

def test_different_seeds_give_different_runs():
    """Different seeds should (almost surely) produce different outcomes."""
    a = simulate(n_spins=50_000, seed=1)
    b = simulate(n_spins=50_000, seed=2)
    assert a["total_win"] != b["total_win"]

def test_invalid_spin_count_raises():
    """Guard clause: non-positive spin counts must raise ValueError."""
    with pytest.raises(ValueError):
        simulate(n_spins=0, seed=42)