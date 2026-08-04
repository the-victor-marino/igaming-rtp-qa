"""
RNG provider for the slot engine.

CRITICAL: real-money games MUST use a cryptographically secure RNG. A standard
PRNG (Mersenne Twister / random.Random) is statistically uniform but fully
PREDICTABLE once its output is observed, which enables real-world cheating.
`secrets` / SystemRandom draws from the OS CSPRNG and has no recoverable state.
"""
import secrets
from random import SystemRandom

def make_secure_rng():
    """Return a cryptographically secure random generator."""
    return SystemRandom()

def next_word(rng):
    """One 32-bit draw from a secure generator (used by the reel selector)."""
    return rng.getrandbits(32)

def secure_randbelow(n):
    """Uniform integer in [0, n) from the OS CSPRNG — for picking reel stops."""
    return secrets.randbelow(n)