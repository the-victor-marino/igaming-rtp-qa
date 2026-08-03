# 🎰 iGaming RTP QA Pipeline

> it proves the audit actually **catches** an unfair RNG, rather than passing
> everything blindly.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+

### Installation

1. Clone the repo

git clone https://github.com/YOUR_USERNAME/igaming-rtp-qa.git
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

## 🧠 Key Concepts Demonstrated

- **iGaming domain knowledge** — RTP, house edge, RNG fairness, Monte Carlo methods.
- **Statistical QA** — chi-square goodness-of-fit testing (lab-grade fairness auditing).
- **Test design** — positive, negative, boundary, and reproducibility tests.
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
