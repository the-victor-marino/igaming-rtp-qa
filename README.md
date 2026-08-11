# 🎰 iGaming RTP QA Pipeline

> it proves the audit actually **catches** an unfair RNG, rather than passing
> everything blindly.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+

### Installation

1. Clone the repo

git clone https://github.com/the-victor-marino/igaming-rtp-qa.git
 cd igaming-rtp-qa

2. Create & activate a virtual environment

python -m venv .venv source .venv/bin/activate # Windows: .venv\Scripts\activate

3. Install dependencies

pip install -r requirements.txt


### Run the test suite

pytest -v --cov=src


### Generate the convergence chart

python run_simulation.py

---

## 🧪 What the Test Suite Verifies

The suite is deliberately layered — from pure maths, through player experience,
to adversarial security — mirroring how fairness QA actually works in regulated
iGaming.

| Test file | Category | What it guarantees |
|-----------|----------|--------------------|
| `test_rtp.py` | Correctness | Theoretical RTP matches the hand-calculated value; simulated RTP converges within tolerance; results are **reproducible** with a fixed seed. |
| `test_payouts.py` | Integrity | Strip counts and payouts stay aligned; probabilities sum to 1; total bet/win accounting is always correct; winnings are never negative. |
| `test_volatility.py` | Player experience | Variance is positive and consistent with σ; hit frequency is a valid probability; simulated variance converges on theory; the volatility index scales with confidence. |
| `test_rng_fairness.py` | Statistical fairness | The RNG passes a chi-square fairness audit **and** a deliberately rigged distribution is correctly *rejected* (negative testing). |
| `test_player_behaviour.py` | Games & gamers | **Gambler's Ruin** — a finite bankroll almost always ends in ruin over a long session (house edge), while short sessions can still end in profit; sessions halt cleanly when funds run out. |
| `test_responsible_gambling.py` | Regulatory / player protection | A player who hits their **loss limit** is stopped, and that limit is never exceeded across many players — reflecting UKGC/MGA player-protection requirements. |
| `test_destructive_rng_predictability.py` | 🔥 Security / destructive | Proves a non-cryptographic PRNG (Mersenne Twister) is **fully predictable** via state recovery — the real slot-machine cheating attack — and guards that the production RNG is a CSPRNG that resists it. |

> Two tests are especially deliberate. The **negative fairness test** proves the
> audit actually *catches* an unfair RNG rather than passing everything blindly.
> The **destructive predictability test** proves the deeper point that
> **statistical fairness ≠ security**: an RNG can be perfectly uniform yet
> completely exploitable.

---

## ⚙️ Continuous Integration

Every push and pull request to `main` triggers the
[GitHub Actions pipeline](.github/workflows/ci.yml), which:

1. Runs the full pytest suite across **Python 3.11 and 3.12**.
2. Reports test coverage.
3. Regenerates the RTP convergence chart.
4. Uploads the test results and chart as downloadable **artifacts**.

A red build immediately signals a fairness regression — for example, if a
developer accidentally changes a payout value, the RTP test fails and the merge
is blocked.

---

## 🔐 Security & Destructive Testing

Passing a chi-square fairness test tells you an RNG is *uniform* — it does **not**
tell you it's *unpredictable*. This distinction is the root cause of the most
famous real-world slot-machine cheating: organised groups recorded spins,
reconstructed the machine's pseudo-random generator, and predicted exactly when
it would pay out.

This project reproduces that attack as a working destructive test:

1. **Observe** 624 consecutive 32-bit outputs from a Mersenne Twister (MT19937)
   generator — the same algorithm behind Python's `random` module.
2. **Reconstruct** the generator's entire internal state by reversing MT's
   tempering transform (`tests/attacker.py`).
3. **Predict** every subsequent spin with 100% accuracy — including timing the
   next jackpot.

The attack **succeeds**, proving the vulnerability. The suite then guards the
fix: the production RNG (`src/rng.py`) uses a **cryptographically secure**
generator (`secrets` / `SystemRandom`) drawn from the OS entropy pool, which has
no recoverable state and defeats the same attack.

> **Design note:** a seeded, reproducible PRNG is used **only** for the
> deterministic simulation and tests. Real-money spin selection uses the CSPRNG.
> Knowing *why* seeding is safe in one context and dangerous in the other is the
> core insight this test demonstrates.

---

## 🧠 Key Concepts Demonstrated

- **iGaming domain knowledge** — RTP, house edge, volatility, hit frequency, RNG fairness, Monte Carlo methods.
- **Games & gamers insight** — Gambler's Ruin, short- vs long-term variance, and realistic player session modelling.
- **Regulatory awareness** — responsible-gambling controls (loss limits) as required in UKGC/MGA markets.
- **Statistical QA** — chi-square goodness-of-fit testing (lab-grade fairness auditing).
- **Security & adversarial testing** — RNG state-recovery attack; the critical distinction between *statistical fairness* and *cryptographic unpredictability*.
- **Test design** — positive, negative, boundary, reproducibility, and destructive tests.
- **DevOps / CI** — automated multi-version testing, coverage, and artifacts.
- **Clean architecture** — game logic (`src/`) fully decoupled from tests (`tests/`).

---

## 🔭 Possible Extensions

- Add a **volatility / variance** metric alongside RTP.
- Support **multi-payline** games and scatter/wild symbols.
- Extend the audit to other game types (roulette, blackjack).
- Add a **serial-correlation / runs test** for deeper RNG analysis.

---

## 📄 License

Released under the MIT License. See [`LICENSE`](https://mit-license.org/license.txt) for details.

---

## 👤 Author

**Victor Marino** - QA Engineer specialising in Game & iGaming testing.
[LinkedIn](https://www.linkedin.com/in/the-victor-marino/)
