"""Tests that audit the fairness/randomness of the RNG."""

import pytest

from src.slot_engine import simulate
from src.rng_audit import chi_square_fairness, does_not_reject_distribution

def test_rng_passes_chi_square():
    """Observed symbol distribution must pass the fairness audit (p > 0.05)."""
    result = simulate(n_spins=500_000, seed=42)
    chi2, p_value = chi_square_fairness(result["symbol_counts"])
    assert does_not_reject_distribution(p_value), f"RNG failed fairness test (chi2={chi2:.3f}, p={p_value:.4f})"

def test_fairness_helper_interpretation():
    """does_not_reject_distribution must correctly interpret p-values against alpha."""
    assert does_not_reject_distribution(0.20) is True
    assert does_not_reject_distribution(0.01) is False

def test_biased_distribution_is_detected():
    """A deliberately skewed distribution must FAIL the fairness test.

    This proves the audit actually detects bias, not just passes everything.
    """
    # Expected ratios are 6:5:4:3:2; feed a wildly wrong distribution instead.
    rigged_counts = [100_000, 100_000, 100_000, 100_000, 100_000]
    _, p_value = chi_square_fairness(rigged_counts)
    assert not does_not_reject_distribution(p_value), "Audit failed to detect a biased distribution!"

def test_empty_observations_raise():
    """Auditing with no observations must raise ValueError."""
    with pytest.raises(ValueError):
        chi_square_fairness([0, 0, 0, 0, 0])