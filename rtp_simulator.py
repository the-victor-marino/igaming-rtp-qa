import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import chisquare

def run_rtp_simulation():
    # ==========================================
    # 1. DEFINE SLOT PARAMETERS
    # ==========================================
    symbols = ['Cherry', 'Lemon', 'Bell', 'Bar', 'Seven']
    counts = np.array([6, 5, 4, 3, 2])
    payouts = np.array([5, 10, 15, 25, 50])
    total_symbols = 20

    # Probability of each symbol landing on a single reel
    probs = counts / total_symbols

    # ==========================================
    # 2 & 3. COMPUTE THEORETICAL RTP
    # ==========================================
    # Reels are independent, so prob of 3-of-a-kind is p^3
    prob_3_of_a_kind = probs ** 3
    expected_payouts = prob_3_of_a_kind * payouts
    theoretical_rtp_pct = np.sum(expected_payouts) * 100

    # ==========================================
    # 4. MONTE CARLO SIMULATION
    # ==========================================
    num_spins = 2_000_000
    print(f"Starting simulation of {num_spins:,} spins...")

    np.random.default_rng(42)

    # Fast simulation: generate 3 arrays of random indices based on symbol probabilities
    reel1 = np.random.choice(len(symbols), size=num_spins, p=probs)
    reel2 = np.random.choice(len(symbols), size=num_spins, p=probs)
    reel3 = np.random.choice(len(symbols), size=num_spins, p=probs)

    # Identify winning spins (3 identical symbols)
    wins = (reel1 == reel2) & (reel2 == reel3)
    win_amounts = np.zeros(num_spins)
    win_amounts[wins] = payouts[reel1[wins]]

    # Calculate cumulative RTP across all spins
    cumulative_wins = np.cumsum(win_amounts)
    cumulative_bets = np.arange(1, num_spins + 1)
    cumulative_rtp = (cumulative_wins / cumulative_bets) * 100

    # ==========================================
    # 5. GENERATE CONVERGENCE CHART
    # ==========================================
    plt.figure(figsize=(10, 6), dpi=200)

    plt.plot(cumulative_bets, cumulative_rtp,
             label='Simulated Cumulative RTP', color='#2196F3')

    plt.axhline(theoretical_rtp_pct, color='#F44336', linestyle='--', linewidth=2,
                label=f'Theoretical RTP ({theoretical_rtp_pct:.4f}%)')

    plt.xscale('log')
    plt.xlabel('Number of Spins (Log Scale)', fontsize=12)
    plt.ylabel('Cumulative RTP (%)', fontsize=12)
    plt.title('Slot RTP Convergence: Simulated vs Theoretical', fontsize=14)
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.legend(fontsize=11)

    plt.tight_layout()
    plt.savefig('rtp_convergence.png')
    print("-> Chart saved as 'rtp_convergence.png'")

    # ==========================================
    # 6. CHI-SQUARE TEST & SUMMARY REPORT
    # ==========================================
    all_symbols = np.concatenate([reel1, reel2, reel3])
    observed_counts = np.bincount(all_symbols, minlength=len(symbols))
    expected_counts = probs * (num_spins * 3)

    chi2_stat, p_val = chisquare(f_obs=observed_counts, f_exp=expected_counts)
    alpha = 0.05
    pass_fail = "PASS (Fair RNG)" if p_val > alpha else "FAIL (Biased RNG)"

    final_rtp = cumulative_rtp[-1]
    diff = abs(theoretical_rtp_pct - final_rtp)

    print("\n" + "="*40)
    print("           RTP SUMMARY REPORT           ")
    print("="*40)
    print(f"Theoretical RTP:       {theoretical_rtp_pct:.4f}%")
    print(f"Final Simulated RTP:   {final_rtp:.4f}%")
    print(f"Absolute Difference:   {diff:.4f}%")

    print("\n" + "="*40)
    print("           RNG FAIRNESS CHECK           ")
    print("="*40)
    print(f"Observed Frequencies:  {observed_counts}")
    print(f"Expected Frequencies:  {expected_counts.astype(int)}")
    print(f"Chi-square Statistic:  {chi2_stat:.4f}")
    print(f"P-value:               {p_val:.4e}")
    print(f"Result:                {pass_fail} at alpha={alpha}")
    print("="*40 + "\n")

if __name__ == "__main__":
    run_rtp_simulation()