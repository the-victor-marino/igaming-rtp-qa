# iGaming RTP QA Pipeline

A small three-reel slot model for demonstrating game QA. It tests payout rules, integer-credit wallet integrity, a session net-loss limit, theoretical versus simulated RTP, symbol frequencies, and an illustrative attack against Mersenne Twister. This is a portfolio model, not a certified game or RNG audit.

## Run

Requires Python 3.11 or 3.12.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pytest -q
python run_simulation.py
```

The report script writes the chart to `rtp_convergence.png` and `reports/`. The GitHub Actions workflow runs tests and creates a simulation artifact on pushes and pull requests to `master`.

## Model and test strategy

- `src/slot_engine.py`: weighted, independent reel stops and exact three-of-a-kind payouts. `spin_payout()` uses the OS-backed `SystemRandom` by default; a caller may inject an RNG for deterministic tests.
- `src/wallet.py`: integer credits, checked stakes and winnings, a lock around each balance operation, and player sessions. A seeded session uses `random.Random` **only for repeatable experiments**. An unseeded session uses the secure provider.
- `src/rng_audit.py`: chi-square goodness-of-fit on marginal symbol frequencies. A non-rejection at a chosen significance level is not proof of fairness, independence, or unpredictability.
- `simulate()` is a separate vectorized NumPy research harness. Its seeded results are reproducible; it is not the secure production spin path.
- `tests/`: exact payout examples, malformed inputs, concurrent bets, loss-limit boundaries, seeded RTP, deliberately biased observations, transition dependence with positive and negative controls, and MT19937 state recovery.

The session loss limit is **net loss relative to the starting balance**. A bet is rejected if losing that entire stake could push net loss above the limit. Balances and stakes use integer credits; applications that accept currency should convert to minor units at the boundary.

## Interpreting the evidence

The theoretical RTP is computed from each symbol's cubed single-reel probability and its payout multiplier. The seeded Monte Carlo test checks proximity for one specified configuration. The chi-square test checks a single marginal distribution; its negative control demonstrates detection of a large bias. These tests do not certify a live game. The MT19937 test receives raw 32-bit outputs, reconstructs state, and predicts future outputs; ordinary players do not generally observe those raw words. The secure-path test checks integration with `SystemRandom`, not a proof of cryptographic security.

CI reports failures and uploads artifacts. Merge protection, if desired, must be configured as a repository ruleset.

## Further QA work

A production system would need transactional persistence across processes, recovery from failed payouts after a debit, time-scoped responsible-gambling limits, monitoring, a full reel mapping review, and independent RNG certification. Statistical extensions could test cross-reel independence and runs with a documented multiple-testing policy.

**Victor Marino** · [LinkedIn](https://www.linkedin.com/in/the-victor-marino/)
