"""
rng_audit.py
------------
RNG fairness auditing utilities.

Provides a chi-square goodness-of-fit test to check whether the observed
symbol distribution matches the expected (weighted) distribution — the same
category of statistical check used by certification labs such as GLI/eCOGRA.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import chisquare

from .slot_engine import SlotConfig, DEFAULT_CONFIG, symbol_probabilities

def chi_square_fairness(
    observed_counts: np.ndarray,
    config: SlotConfig = DEFAULT_CONFIG,
) -> tuple[float, float]:
    """Run a chi-square goodness-of-fit test on observed symbol counts.

    Parameters
    ----------
    observed_counts : np.ndarray
        Observed count of each symbol (order must match config.symbols).
    config : SlotConfig
        Game configuration providing the expected probabilities.

    Returns
    -------
    (chi2_statistic, p_value)
    """
    observed = np.asarray(observed_counts, dtype=float)
    if observed.shape != (len(config.symbols),) or not np.all(np.isfinite(observed)) or np.any(observed < 0):
        raise ValueError("counts must be finite and nonnegative for every symbol")
    total = observed.sum()
    if total <= 0:
        raise ValueError("observed_counts must contain at least one observation")

    expected = symbol_probabilities(config) * total
    chi2_stat, p_value = chisquare(f_obs=observed, f_exp=expected)
    return float(chi2_stat), float(p_value)

def does_not_reject_distribution(p_value: float, alpha: float = 0.05) -> bool:
    """Interpret a p-value: True means we do NOT reject the fairness hypothesis."""
    if not (0 <= p_value <= 1 and 0 < alpha < 1):
        raise ValueError("invalid p-value or significance level")
    return p_value >= alpha

def is_fair(p_value: float, alpha: float = 0.05) -> bool:
    """Legacy alias; a passing test does not establish fairness."""
    return does_not_reject_distribution(p_value, alpha)


def transition_independence(draws, config: SlotConfig = DEFAULT_CONFIG) -> tuple[float, float]:
    """Chi-square independence test for successive categorical draws.

    Diagnostic only: significance and power depend on sample size and hypothesis.
    """
    from scipy.stats import chi2_contingency
    values = np.asarray(draws)
    k = len(config.symbols)
    if values.ndim != 1 or len(values) < 2 or not np.issubdtype(values.dtype, np.integer) or np.any((values < 0) | (values >= k)):
        raise ValueError("draws must be at least two valid symbol indices")
    pairs = np.zeros((k, k), dtype=int)
    np.add.at(pairs, (values[:-1], values[1:]), 1)
    if np.any(pairs.sum(axis=0) == 0) or np.any(pairs.sum(axis=1) == 0):
        raise ValueError("every symbol needs an observed transition")
    chi2, p, _, _ = chi2_contingency(pairs)
    return float(chi2), float(p)
