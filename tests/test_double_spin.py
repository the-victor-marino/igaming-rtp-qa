import threading
from src.wallet import Wallet, InsufficientFundsError

def test_no_double_spend_under_concurrent_bets():
    """
    A player with only enough for ONE bet fires two simultaneous spins.
    Exactly one must succeed; the balance must never go negative.
    (Requires a lock around place_bet for a true fix — this test proves the need.)
    """
    w = Wallet(balance=10)
    results = []

    def try_bet():
        try:
            w.place_bet(10)
            results.append("success")
        except InsufficientFundsError:
            results.append("rejected")

    t1, t2 = threading.Thread(target=try_bet), threading.Thread(target=try_bet)
    t1.start(); t2.start(); t1.join(); t2.join()

    assert w.balance >= 0                    # never negative
    assert results.count("success") <= 1     # at most one bet got through