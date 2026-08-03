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
    total = observed.sum()
    if total <= 0:
        raise ValueError("observed_counts must contain at least one observation")

    expected = symbol_probabilities(config) * total
    chi2_stat, p_value = chisquare(f_obs=observed, f_exp=expected)
    return float(chi2_stat), float(p_value)

def is_fair(p_value: float, alpha: float = 0.05) -> bool:
    """Interpret a p-value: True means we do NOT reject the fairness hypothesis."""
    return p_value > alpha