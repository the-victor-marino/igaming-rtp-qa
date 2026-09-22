"""Deterministic positive and negative controls for transition dependence."""
import numpy as np
from src.rng_audit import transition_independence, does_not_reject_distribution
from src.slot_engine import symbol_probabilities


def test_seeded_independent_draws_and_repeated_draws():
    rng = np.random.default_rng(912)
    independent = rng.choice(5, 100_000, p=symbol_probabilities())
    _, p_independent = transition_independence(independent)
    _, p_repeated = transition_independence(np.repeat(independent, 2))
    assert does_not_reject_distribution(p_independent)
    assert not does_not_reject_distribution(p_repeated)
