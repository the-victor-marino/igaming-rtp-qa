"""Three-reel slot model. Money and payout multipliers are integer credits."""
from dataclasses import dataclass
import numpy as np
from .rng import make_secure_rng


@dataclass(frozen=True)
class SlotConfig:
    symbols: tuple[str, ...] = ("Cherry", "Lemon", "Bell", "Bar", "Seven")
    strip_counts: tuple[int, ...] = (6, 5, 4, 3, 2)
    payouts: tuple[int, ...] = (5, 10, 15, 25, 50)
    bet: int = 1

    def __post_init__(self):
        if not self.symbols or len(self.symbols) != len(self.strip_counts) or len(self.symbols) != len(self.payouts):
            raise ValueError("symbols, strip_counts and payouts must have equal nonzero length")
        if len(set(self.symbols)) != len(self.symbols) or any(not isinstance(s, str) or not s for s in self.symbols):
            raise ValueError("symbols must be distinct nonempty strings")
        if any(type(c) is not int or c <= 0 for c in self.strip_counts):
            raise ValueError("strip counts must be positive integers")
        if any(type(p) is not int or p < 0 for p in self.payouts):
            raise ValueError("payouts must be nonnegative integers")
        if type(self.bet) is not int or self.bet <= 0:
            raise ValueError("bet must be a positive integer")

    @property
    def reel_length(self):
        return sum(self.strip_counts)


DEFAULT_CONFIG = SlotConfig()


def symbol_probabilities(config=DEFAULT_CONFIG):
    return np.asarray(config.strip_counts, dtype=float) / config.reel_length


def payout_for_reels(reels, config=DEFAULT_CONFIG):
    """Return the payout multiplier for three symbols on the centre payline."""
    if len(reels) != 3 or any(symbol not in config.symbols for symbol in reels):
        raise ValueError("exactly three configured symbols are required")
    return config.payouts[config.symbols.index(reels[0])] if reels[0] == reels[1] == reels[2] else 0


def spin_payout(rng=None, config=DEFAULT_CONFIG):
    """Select independent weighted reel stops; secure OS RNG is the default."""
    if rng is None:
        rng = make_secure_rng()
    strip = tuple(symbol for symbol, count in zip(config.symbols, config.strip_counts) for _ in range(count))
    return payout_for_reels(tuple(strip[rng.randrange(len(strip))] for _ in range(3)), config)


def theoretical_rtp(config=DEFAULT_CONFIG):
    """Expected return divided by the configured stake."""
    return float(np.sum(symbol_probabilities(config) ** 3 * np.asarray(config.payouts)) / config.bet)


def simulate(n_spins, config=DEFAULT_CONFIG, seed=None):
    """Vectorized seeded research simulation, separate from the secure spin path."""
    if type(n_spins) is not int or n_spins <= 0:
        raise ValueError("n_spins must be a positive integer")
    rng = np.random.default_rng(seed)
    reels = rng.choice(len(config.symbols), size=(n_spins, 3), p=symbol_probabilities(config))
    wins = (reels[:, 0] == reels[:, 1]) & (reels[:, 1] == reels[:, 2])
    amounts = np.zeros(n_spins, dtype=float)
    amounts[wins] = np.asarray(config.payouts)[reels[wins, 0]]
    cumulative_win = np.cumsum(amounts)
    cumulative_rtp = cumulative_win / (np.arange(1, n_spins + 1) * config.bet)
    return {"simulated_rtp": float(cumulative_rtp[-1]), "cumulative_rtp": cumulative_rtp,
            "symbol_counts": np.bincount(reels.ravel(), minlength=len(config.symbols)),
            "total_win": float(cumulative_win[-1]), "total_bet": float(n_spins * config.bet)}
