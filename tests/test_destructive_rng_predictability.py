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
    JACKPOT_THRESHOLD = 0xFF000000  # illustrative high-value draw threshold

    observed = [victim.getrandbits(32) for _ in range(624)]
    clone = clone_from_observations(observed)

    # Attacker scans the FUTURE for the next jackpot spin.
    predicted_jackpot_index = next(
        i for i in range(10_000) if clone.getrandbits(32) >= JACKPOT_THRESHOLD
    )

    # Victim plays forward; check the attacker's prediction was correct.
    future = [victim.getrandbits(32) for _ in range(10_000)]
    assert future[predicted_jackpot_index] >= JACKPOT_THRESHOLD

def test_default_spin_uses_secure_rng(monkeypatch):
    """The actual spin path requests the secure provider and consumes three draws."""
    from src import slot_engine
    from src.rng import make_secure_rng
    from random import SystemRandom
    assert isinstance(make_secure_rng(), SystemRandom)

    class RecordingRNG:
        calls = 0
        def randrange(self, limit):
            assert limit == 20
            self.calls += 1
            return 0

    recorder = RecordingRNG()
    monkeypatch.setattr(slot_engine, "make_secure_rng", lambda: recorder)
    assert slot_engine.spin_payout() == 5
    assert recorder.calls == 3
