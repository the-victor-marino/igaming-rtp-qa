"""Generate a reproducible game QA report and its supporting charts."""

import argparse
from pathlib import Path
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")  # Works on CI and machines without a display.
import matplotlib.pyplot as plt
import numpy as np

from src.report import build_report, read_junit
from src.rng_audit import chi_square_fairness, does_not_reject_distribution
from src.slot_engine import DEFAULT_CONFIG, simulate, symbol_probabilities, theoretical_rtp


def save_convergence(result, theory, n_spins, destination):
    cumulative_rtp = result["cumulative_rtp"] * 100
    idx = np.unique(np.geomspace(1, n_spins, num=1000, dtype=int)) - 1
    fig, ax = plt.subplots(figsize=(10, 5.4), dpi=150)
    ax.plot(idx + 1, cumulative_rtp[idx], label="Observed cumulative RTP", color="#008e88", linewidth=2)
    ax.axhline(theory * 100, color="#e65b55", linestyle="--", linewidth=2,
               label=f"Expected RTP: {theory*100:.4f}%")
    ax.set_xscale("log")
    ax.set_xlabel("Number of spins (log scale)")
    ax.set_ylabel("Cumulative RTP (%)")
    ax.set_title("Return to player: observed versus expected", loc="left", weight="bold")
    ax.grid(alpha=0.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(destination)
    fig.savefig("rtp_convergence.png")  # Keep the existing image path working.
    plt.close(fig)


def save_frequencies(result, n_spins, destination):
    config = DEFAULT_CONFIG
    expected = symbol_probabilities(config) * 100
    observed = result["symbol_counts"] / (3 * n_spins) * 100
    x = np.arange(len(config.symbols))
    fig, ax = plt.subplots(figsize=(10, 4.7), dpi=150)
    ax.bar(x - 0.19, expected, width=0.38, color="#102b43", label="Expected")
    ax.bar(x + 0.19, observed, width=0.38, color="#008e88", label="Observed")
    ax.set_xticks(x, config.symbols)
    ax.set_ylabel("Share of all reel draws (%)")
    ax.set_title("Symbol frequency on the three reels", loc="left", weight="bold")
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(destination)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the game QA evidence report")
    parser.add_argument("--junit", type=Path, help="Use an existing pytest JUnit XML file (CI uses this to avoid rerunning tests)")
    args = parser.parse_args()
    n_spins, seed = 2_000_000, 42
    reports = Path("reports")
    reports.mkdir(exist_ok=True)

    if args.junit is None:
        junit = reports / "report-tests.xml"
        run = subprocess.run([sys.executable, "-m", "pytest", "-q", f"--junitxml={junit}"],
                             text=True, capture_output=True, check=False)
        print(run.stdout)
        if run.stderr:
            print(run.stderr, file=sys.stderr)
    else:
        junit = args.junit
        run = None
    tests = read_junit(junit)

    config = DEFAULT_CONFIG
    theory = theoretical_rtp(config)
    result = simulate(n_spins=n_spins, config=config, seed=seed)
    chi2, p_value = chi_square_fairness(result["symbol_counts"], config)
    probs = symbol_probabilities(config)
    win_probability = probs ** 3
    payouts = np.asarray(config.payouts)
    per_spin_mean = np.sum(win_probability * payouts)
    per_spin_variance = np.sum(win_probability * payouts ** 2) - per_spin_mean ** 2
    margin = 1.96 * np.sqrt(per_spin_variance / n_spins) / config.bet
    metrics = {
        "spins": n_spins, "seed": seed, "theory": theory,
        "observed": result["simulated_rtp"],
        "difference_pp": abs(theory - result["simulated_rtp"]) * 100,
        "wins": int(np.sum(result["win_counts"])),
        "observed_hit": float(np.sum(result["win_counts"]) / n_spins),
        "theoretical_hit": float(np.sum(win_probability)),
        "band_low": theory - margin, "band_high": theory + margin,
        "in_band": abs(result["simulated_rtp"] - theory) <= margin,
        "chi2": chi2, "p_value": p_value,
        "frequency_ok": does_not_reject_distribution(p_value),
    }
    convergence = reports / "rtp_convergence.png"
    frequencies = reports / "symbol_frequencies.png"
    save_convergence(result, theory, n_spins, convergence)
    save_frequencies(result, n_spins, frequencies)
    html = build_report(result, metrics, tests, convergence, frequencies, config)
    destination = reports / "qa_report.html"
    destination.write_text(html, encoding="utf-8")

    print(f"Expected RTP: {theory*100:.4f}%")
    print(f"Observed RTP: {result['simulated_rtp']*100:.4f}%")
    print(f"Frequency check: {'not rejected' if metrics['frequency_ok'] else 'rejected'} (p={p_value:.4g})")
    print(f"Tests: {tests['passed']}/{tests['tests']} passed ({tests['status']})")
    print(f"Open the full report: {destination}")
    if run is not None and run.returncode:
        return run.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
