"""Integer-credit wallet and deterministic or secure game sessions."""
import random
from threading import Lock
from .rng import make_secure_rng
from .slot_engine import DEFAULT_CONFIG, spin_payout


class InvalidBetError(ValueError):
    pass


class InsufficientFundsError(ValueError):
    pass


def _credits(value, name, allow_zero=False):
    if type(value) is not int or value < 0 or (not allow_zero and value == 0):
        raise InvalidBetError(f"{name} must be {'nonnegative' if allow_zero else 'positive'} integer credits")


class Wallet:
    def __init__(self, balance, min_bet=1, max_bet=100):
        _credits(balance, "balance", allow_zero=True)
        _credits(min_bet, "min_bet")
        _credits(max_bet, "max_bet")
        if min_bet > max_bet:
            raise ValueError("min_bet exceeds max_bet")
        self.balance, self.min_bet, self.max_bet = balance, min_bet, max_bet
        self._lock = Lock()

    def place_bet(self, bet):
        _credits(bet, "bet")
        with self._lock:
            if not self.min_bet <= bet <= self.max_bet:
                raise InvalidBetError("bet outside table limits")
            if bet > self.balance:
                raise InsufficientFundsError("insufficient balance")
            self.balance -= bet
        return bet

    def credit(self, amount):
        _credits(amount, "amount", allow_zero=True)
        with self._lock:
            self.balance += amount
        return amount


def _session_inputs(starting_balance, bet, max_spins):
    _credits(starting_balance, "starting_balance", allow_zero=True)
    _credits(bet, "bet")
    if type(max_spins) is not int or max_spins < 0:
        raise ValueError("max_spins must be a nonnegative integer")


def _rng(seed):
    return make_secure_rng() if seed is None else random.Random(seed)


def play_session(starting_balance, bet, max_spins, seed=None, config=DEFAULT_CONFIG, spin_fn=spin_payout):
    _session_inputs(starting_balance, bet, max_spins)
    rng = _rng(seed)
    wallet = Wallet(starting_balance, max_bet=max(100, bet))
    spins_played, peak_balance = 0, starting_balance
    for _ in range(max_spins):
        if wallet.balance < bet:
            break
        wallet.place_bet(bet)
        multiple = spin_fn(rng, config)
        _credits(multiple, "payout multiplier", allow_zero=True)
        wallet.credit(bet * multiple)
        spins_played += 1
        peak_balance = max(peak_balance, wallet.balance)
    return {"final_balance": wallet.balance, "spins_played": spins_played,
            "peak_balance": peak_balance, "went_broke": wallet.balance < bet}


def play_session_with_loss_limit(starting_balance, bet, loss_limit, max_spins, seed=None,
                                 config=DEFAULT_CONFIG, spin_fn=spin_payout):
    """Cap net loss from session start, rejecting a stake that could exceed the cap."""
    _session_inputs(starting_balance, bet, max_spins)
    _credits(loss_limit, "loss_limit", allow_zero=True)
    rng = _rng(seed)
    wallet = Wallet(starting_balance, max_bet=max(100, bet))
    spins_played, stopped_by_limit = 0, False
    for _ in range(max_spins):
        if starting_balance - wallet.balance + bet > loss_limit:
            stopped_by_limit = True
            break
        if wallet.balance < bet:
            break
        wallet.place_bet(bet)
        multiple = spin_fn(rng, config)
        _credits(multiple, "payout multiplier", allow_zero=True)
        wallet.credit(bet * multiple)
        spins_played += 1
    return {"final_balance": wallet.balance, "spins_played": spins_played,
            "stopped_by_limit": stopped_by_limit}
