"""
Adversary toolkit: reconstructs the internal state of an MT19937 (Mersenne
Twister) PRNG from its observed 32-bit outputs, then predicts all future output.

This is the same class of attack used in real-world slot-machine cheating:
record enough spins -> recover RNG state -> predict when the machine pays out.
"""
import random

def _undo_right_shift(value, shift):
    result = value
    for _ in range((32 // shift) + 1):
        result = value ^ (result >> shift)
    return result

def _undo_left_shift(value, shift, mask):
    result = value
    for _ in range((32 // shift) + 1):
        result = value ^ ((result << shift) & mask)
    return result

def untemper(y):
    """Reverse MT19937's tempering to recover one word of internal state."""
    y = _undo_right_shift(y, 18)
    y = _undo_left_shift(y, 15, 0xEFC60000)
    y = _undo_left_shift(y, 7, 0x9D2C5680)
    y = _undo_right_shift(y, 11)
    return y

def clone_from_observations(observed_words):
    """
    Given 624 consecutive 32-bit outputs from a victim MT19937 generator,
    return a cloned random.Random that will produce identical future output.
    """
    if len(observed_words) < 624:
        raise ValueError("Need at least 624 consecutive 32-bit outputs to clone MT19937.")

    state = [untemper(w) for w in observed_words[:624]]
    clone = random.Random()
    # Python's state tuple: (version, (624 state words + index), gauss_next)
    clone.setstate((3, tuple(state + [624]), None))
    return clone