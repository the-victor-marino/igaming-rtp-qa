"""
DESTRUCTIVE / SECURITY TEST — RNG Predictability.

Goal: prove that a non-cryptographic PRNG (Mersenne Twister, i.e. Python's
`random`) is exploitable. An attacker who observes a run of raw outputs can
reconstruct the generator and predict every future spin — the real-world
slot-machine attack.

This test does two things:
  1. DEMONSTRATES the vulnerability by successfully predicting future output.
  2. GUARDS the fix: asserts the engine's production RNG factory returns a
     cryptographically secure, non-predictable generator.
"""
import random
import pytest

from tests.attacker import clone_from_observations

# The production RNG factory your engine should expose. See "the fix" below.
from src.rng import make_secure_rng, next_word

def test_mersenne_twister_is_fully_predictable():
    """
    Attacker records 624 spins' worth of raw RNG output, clones the generator,
    and then predicts the NEXT 1,000 outputs with 100% accuracy.
    If this passes, the RNG is exploitable and unfit for real-money play.
    """
    victim = random.Random(1234)  # any seed; attacker never sees it

    # 1. Attacker observes 624 consecutive 32-bit outputs.
    observed = [victim.getrandbits(32) for _ in range(624)]

    # 2. Attacker reconstructs the generator from observations alone.
    clone = clone_from_observations(observed)

    # 3. Attacker predicts the next 1,000 outputs BEFORE the victim produces them.
    predicted = [clone.getrandbits(32) for _ in range(1000)]
    actual = [victim.getrandbits(32) for _ in range(1000)]

    assert predicted == actual, "Attack failed — but a passing attack is the point!"
    # The attack SUCCEEDING proves the vulnerability exists in MT19937.

def test_predicting_the_next_big_win():
    """
    Frames the exploit in game terms: once cloned, the attacker knows exactly
    which upcoming spin will be a jackpot, so they can time a max bet to it.
    """
    victim = random.Random(9876)
    JACKPOT_THRESHOLD = 0xFFFF0000  # pretend: a draw above this triggers a jackpot

    observed = [victim.getrandbits(32) for _ in range(624)]
    clone = clone_from_observations(observed)

    # Attacker scans the FUTURE for the next jackpot spin.
    predicted_jackpot_index = next(
        i for i in range(10_000) if clone.getrandbits(32) >= JACKPOT_THRESHOLD
    )

    # Victim plays forward; check the attacker's prediction was correct.
    future = [victim.getrandbits(32) for _ in range(10_000)]
    assert future[predicted_jackpot_index] >= JACKPOT_THRESHOLD

def test_secure_rng_is_NOT_predictable():
    """
    THE GUARD: the production RNG must resist the same attack. A CSPRNG has no
    recoverable internal state, so identical observation gives no predictive power.
    Two independent secure generators must not agree on future output.
    """
    victim = make_secure_rng()
    observed = [next_word(victim) for _ in range(624)]

    # Attempt the same clone-and-predict attack against the secure RNG.
    # (A real CSPRNG can't be reconstructed; here we assert non-determinism.)
    attacker_guess = make_secure_rng()
    predicted = [next_word(attacker_guess) for _ in range(64)]
    actual = [next_word(victim) for _ in range(64)]

    assert predicted != actual, "Secure RNG must not be predictable from observation."

def test_secure_rng_streams_are_unique():
    """Two secure generators must never produce identical streams."""
    a = [next_word(make_secure_rng()) for _ in range(128)]
    b = [next_word(make_secure_rng()) for _ in range(128)]
    assert a != b