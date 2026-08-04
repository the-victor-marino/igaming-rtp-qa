"""
Wallet & session model for the slot game.

In iGaming the wallet is the single most safety-critical component — it holds
real money. Every mutation to a balance is guarded, and the balance can NEVER
be corrupted by bad input. These guarantees are what the test suite verifies.
"""
import math
import random

from .slot_engine import DEFAULT_CONFIG, spin_payout   # spin_payout(rng, config) -> bet multiple (0 = loss)

class InvalidBetError(ValueError):
    """Raised when a stake is malformed, non-positive, or outside table limits."""

class InsufficientFundsError(ValueError):
    """Raised when a player tries to stake more than their balance."""

class Wallet:
    """A player's balance with strictly validated debit/credit operations."""

    def __init__(self, balance, min_bet=1, max_bet=100):
        if balance < 0:
            raise ValueError("Opening balance cannot be negative.")
        self.balance = balance
        self.min_bet = min_bet
        self.max_bet = max_bet

    def place_bet(self, bet):
        """
        Debit a stake from the balance. This is the money-critical path, so it
        rejects ANYTHING that isn't a clean, positive, in-range, affordable bet.
        """
        # --- Guard clauses: reject adversarial / malformed input ---
        if isinstance(bet, bool) or not isinstance(bet, (int, float)):
            raise InvalidBetError(f"Bet must be a number, got {type(bet).__name__}.")
        if isinstance(bet, float) and (math.isnan(bet) or math.isinf(bet)):
            raise InvalidBetError("Bet cannot be NaN or infinite.")
        if bet <= 0:
            raise InvalidBetError("Bet must be strictly positive.")
        if bet < self.min_bet or bet > self.max_bet:
            raise InvalidBetError(
                f"Bet {bet} outside table limits [{self.min_bet}, {self.max_bet}]."
            )
        if bet > self.balance:
            raise InsufficientFundsError("Cannot stake more than the current balance.")

        self.balance -= bet
        return bet

    def credit(self, amount):
        """Credit winnings. Winnings can be zero but never negative."""
        if amount < 0:
            raise InvalidBetError("Cannot credit a negative amount.")
        self.balance += amount
        return amount

def play_session(starting_balance, bet, max_spins, seed=None,
                 config=DEFAULT_CONFIG, spin_fn=spin_payout):
    """
    Simulate a realistic player session: keep spinning until the player either
    runs out of affordable balance or hits the spin cap.

    `spin_fn` is injectable so tests can substitute a deterministic outcome.
    Returns a summary dict describing how the session went.
    """
    rng = random.Random(seed)
    wallet = Wallet(starting_balance)
    spins_played = 0
    peak_balance = starting_balance

    for _ in range(max_spins):
        if wallet.balance < bet:
            break  # can no longer afford a spin → effectively broke
        wallet.place_bet(bet)
        payout_multiple = spin_fn(rng, config)   # 0 on a losing spin
        wallet.credit(bet * payout_multiple)
        spins_played += 1
        peak_balance = max(peak_balance, wallet.balance)

    return {
        "final_balance": wallet.balance,
        "spins_played": spins_played,
        "peak_balance": peak_balance,
        "went_broke": wallet.balance < bet,
    }

def play_session_with_loss_limit(starting_balance, bet, loss_limit,
                                 max_spins, seed=None,
                                 config=DEFAULT_CONFIG, spin_fn=spin_payout):
    """
    Responsible-gambling session: enforce a NET LOSS LIMIT. Once the player has
    lost more than `loss_limit`, play stops — protecting the player even if they
    still have funds and want to keep going.
    """
    rng = random.Random(seed)
    wallet = Wallet(starting_balance)
    spins_played = 0
    stopped_by_limit = False

    for _ in range(max_spins):
        net_loss = starting_balance - wallet.balance
        if net_loss >= loss_limit:
            stopped_by_limit = True
            break
        if wallet.balance < bet:
            break
        wallet.place_bet(bet)
        wallet.credit(bet * spin_fn(rng, config))
        spins_played += 1

    return {
        "final_balance": wallet.balance,
        "spins_played": spins_played,
        "stopped_by_limit": stopped_by_limit,
    }