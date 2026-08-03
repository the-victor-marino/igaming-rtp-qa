"""
run_simulation.py
-----------------
Entry point that runs a full 2-million-spin simulation and saves the
RTP convergence chart. Used both for the README screenshot and as a
CI artifact.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless backend so it works on CI servers
import matplotlib.pyplot as plt

from src.slot_engine import theoretical_rtp, simulate
from src.rng_audit import chi_square_fairness, is_fair

def main() -> None:
    n_spins = 2_000_000
    seed = 42  # fixed seed => reproducible chart in CI

    theo = theoretical_rtp()
    result = simulate(n_spins=n_spins, seed=seed)
    sim_rtp = result["simulated_rtp"]
    chi2, p_value = chi_square_fairness(result["symbol_counts"])

    # --- Console report ---
    print("=" * 44)
    print("            RTP QA SUMMARY REPORT")
    print("=" * 44)
    print(f"Theoretical RTP:     {theo * 100:.4f}%")
    print(f"Simulated RTP:       {sim_rtp * 100:.4f}%")
    print(f"Absolute Difference: {abs(theo - sim_rtp) * 100:.4f}%")
    print("-" * 44)
    print(f"Chi-square statistic: {chi2:.4f}")
    print(f"P-value:              {p_value:.4f}")
    print(f"RNG fairness:         {'PASS' if is_fair(p_value) else 'FAIL'}")
    print("=" * 44)

    # --- Convergence chart ---
    cumulative_rtp = result["cumulative_rtp"] * 100
    # Sub-sample points on a log scale to keep the image light and clean.
    idx = np.unique(np.geomspace(1, n_spins, num=1000, dtype=int)) - 1

    plt.figure(figsize=(10, 6), dpi=150)
    plt.plot(idx + 1, cumulative_rtp[idx],
             label="Simulated Cumulative RTP", color="#2196F3")
    plt.axhline(theo * 100, color="#F44336", linestyle="--", linewidth=2,
                label=f"Theoretical RTP ({theo * 100:.4f}%)")
    plt.xscale("log")
    plt.xlabel("Number of Spins (Log Scale)", fontsize=12)
    plt.ylabel("Cumulative RTP (%)", fontsize=12)
    plt.title("Slot RTP Convergence: Simulated vs Theoretical",
              fontsize=14, fontweight="bold")
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.legend(fontsize=11)
    plt.tight_layout()

    os.makedirs("reports", exist_ok=True)
    plt.savefig("rtp_convergence.png")
    plt.savefig(os.path.join("reports", "rtp_convergence.png"))
    print("-> Chart saved to 'rtp_convergence.png' and 'reports/'")

if __name__ == "__main__":
    main()