<div align="center">

# 🎰 Slot QA Lab

**Play the game. Trigger a bug. See the test catch it.**

A Python QA portfolio project exploring payouts, wallet integrity and randomness in a three-reel slot.

[**▶ Try the interactive lab**](https://the-victor-marino.github.io/igaming-rtp-qa/) · [Browse the tests](tests/) · [View CI runs](https://github.com/the-victor-marino/igaming-rtp-qa/actions)

[![QA pipeline](https://github.com/the-victor-marino/igaming-rtp-qa/actions/workflows/ci.yml/badge.svg)](https://github.com/the-victor-marino/igaming-rtp-qa/actions/workflows/ci.yml)

</div>

---

### Try it in 30 seconds

Open the lab → select **Double spending** → click **Send simultaneous bets**.

Watch two requests compete for the same credits, then compare **expected vs. actual** results. You can also change stakes, force reel outcomes and toggle payout or loss-limit bugs.

*The browser lab runs JavaScript demonstrations. The Python test suite runs separately with pytest.*

### What I test

| Area | Risk checked |
| :--- | :--- |
| **Payouts** | Wrong prizes and invalid game inputs |
| **Wallet** | Incorrect balances, invalid stakes and double spending |
| **Loss limits** | A next bet taking session net loss beyond the cap |
| **RTP & randomness** | Return-to-player deviations, biased frequencies, dependence and predictable RNG output |

**Tools:** Python · pytest · NumPy · SciPy · GitHub Actions · JavaScript

### Evidence you can inspect

- **[Automated tests](tests/)** — known outcomes, boundaries and deliberate failure scenarios.
- **[HTML report generator](run_simulation.py)** — test results, two million simulated spins and explanatory charts.
- **[CI workflow](.github/workflows/ci.yml)** — repeats checks on Python 3.11 / 3.12 and uploads reports.

<details>
<summary><strong>Run locally & generate the report</strong></summary>

Clone the repository and open its folder. Use Python 3.11 or 3.12 to match CI.

```bash
git clone https://github.com/the-victor-marino/igaming-rtp-qa.git
cd igaming-rtp-qa
python -m venv .venv
```

**Windows PowerShell**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_simulation.py
```

**macOS / Linux**

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_simulation.py
```

Open **`reports/qa_report.html`** in your browser. The command runs pytest automatically; the HTML includes its charts and can be shared as one file.

To run only the tests, use your virtual environment's Python with `-m pytest -v`.

</details>

<details>
<summary><strong>Code map & model boundaries</strong></summary>

| File | Responsibility |
| :--- | :--- |
| [`src/slot_engine.py`](src/slot_engine.py) | Weighted reels, payouts and RTP simulation |
| [`src/wallet.py`](src/wallet.py) | Integer credits, locked balance operations and session limits |
| [`src/rng_audit.py`](src/rng_audit.py) | Statistical diagnostics |
| [`src/report.py`](src/report.py) | Readable QA evidence |
| [`docs/`](docs/) | Interactive browser lab |

- Normal unseeded spins use OS-backed `SystemRandom`. Seeded sessions and NumPy simulations support repeatable experiments.
- The loss cap measures net loss from the starting balance and checks the full next stake.
- A frequency check does not prove fairness, independence or unpredictability. The MT19937 demonstration assumes access to raw 32-bit outputs.
- This portfolio model is not a certified game. Live use would require durable transactions, payout recovery, time-scoped controls and independent review. CI reports failures; merge protection requires repository rules.

</details>

---

**Victor Marino** · Game production → QA · [LinkedIn](https://www.linkedin.com/in/the-victor-marino/)
