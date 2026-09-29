"""Render a self-contained, readable QA report from measured results."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

from .slot_engine import DEFAULT_CONFIG, symbol_probabilities


def read_junit(path: Path) -> dict:
    """Summarize pytest's JUnit XML without guessing whether tests passed."""
    if not path.is_file():
        return {"status": "Unavailable", "tests": 0, "passed": 0,
                "failed": 0, "skipped": 0, "groups": [],
                "detail": f"No test results found at {path}."}
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return {"status": "Unavailable", "tests": 0, "passed": 0,
                "failed": 0, "skipped": 0, "groups": [],
                "detail": f"Could not read test results at {path}."}
    cases = root.findall(".//testcase")
    groups = {}
    failed = skipped = 0
    for case in cases:
        classname = case.get("classname", "other")
        group = classname.split(".")[-1]
        groups[group] = groups.get(group, 0) + 1
        if case.find("failure") is not None or case.find("error") is not None:
            failed += 1
        elif case.find("skipped") is not None:
            skipped += 1
    total = len(cases)
    passed = total - failed - skipped
    status = "Passed" if passed and failed == 0 else "Failed" if failed else "Unavailable"
    return {"status": status, "tests": total, "passed": passed,
            "failed": failed, "skipped": skipped, "groups": sorted(groups.items()),
            "detail": "Results from pytest JUnit XML."}


def build_report(result: dict, metrics: dict, tests: dict,
                 convergence_png: Path, frequency_png: Path, config=DEFAULT_CONFIG) -> str:
    """Build standalone HTML with inline CSS and images; no network needed."""
    probs = symbol_probabilities(config)
    n = metrics["spins"]
    total_draws = 3 * n
    table_rows = []
    for i, (symbol, count, payout) in enumerate(zip(config.symbols, config.strip_counts, config.payouts)):
        observed_draws = int(result["symbol_counts"][i])
        observed_wins = int(result["win_counts"][i])
        theoretical_wins = n * probs[i] ** 3
        expected_rtp = probs[i] ** 3 * payout / config.bet * 100
        observed_rtp = observed_wins * payout / (n * config.bet) * 100
        table_rows.append(
            f"<tr><th scope='row'>{escape(symbol)}</th><td>{count}/{config.reel_length}</td>"
            f"<td>{probs[i]*100:.2f}%</td><td>{observed_draws/total_draws*100:.2f}%</td>"
            f"<td>{theoretical_wins:,.0f}</td><td>{observed_wins:,}</td>"
            f"<td>{payout}×</td><td>{expected_rtp:.3f}%</td><td>{observed_rtp:.3f}%</td></tr>"
        )
    repo = "https://github.com/the-victor-marino/igaming-rtp-qa"
    test_rows = "".join(
        f"<tr><th scope='row'><a href='{repo}/blob/master/tests/{escape(name, quote=True)}.py'>"
        f"{escape(name)}.py</a></th><td>{count}</td></tr>"
        for name, count in tests["groups"]
    )
    if not test_rows:
        test_rows = "<tr><td colspan='2'>Test details unavailable for this run.</td></tr>"
    def inline_png(path):
        return base64.b64encode(path.read_bytes()).decode("ascii")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    frequency_label = "No frequency mismatch detected" if metrics["frequency_ok"] else "Frequency mismatch detected"
    test_class = "ok" if tests["status"] == "Passed" else "warn"
    p_value = f'{metrics["p_value"]:.4f}' if metrics["p_value"] >= 0.0001 else f'{metrics["p_value"]:.2e}'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Game QA Evidence Report</title>
<style>
:root {{ color-scheme: light; --ink:#102b43; --muted:#536879; --teal:#008e88; --coral:#e65b55; --line:#dbe5e8; --cream:#fcfaf5; }}
* {{ box-sizing:border-box }} body {{ margin:0; background:var(--cream); color:var(--ink); font:16px/1.5 Arial,Helvetica,sans-serif }}
.page {{ max-width:1120px; margin:auto; padding:0 32px 70px }} header {{ background:#102b43; color:white; padding:56px 0 46px }}
header .page {{ padding-bottom:0 }} .eyebrow {{ color:#fbd267; font-size:13px; letter-spacing:.15em; font-weight:700; text-transform:uppercase }}
h1 {{ font-size:clamp(32px,5vw,56px); line-height:1.1; margin:12px 0 16px }} h2 {{ font-size:29px; margin:0 0 12px }} h3 {{ font-size:19px; margin:0 0 8px }}
p {{ margin:0 0 13px }} header p {{ color:#d3eced; max-width:760px; font-size:19px }} .meta {{ margin-top:26px; font-size:13px; color:#b5ced3 }}
section {{ margin-top:48px }} .lead {{ color:var(--muted); max-width:840px }} .grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-top:24px }}
.card,.panel {{ background:white; border:1px solid var(--line); border-radius:13px; padding:22px; box-shadow:0 5px 24px #102b4308 }}
.card strong {{ display:block; font-size:clamp(24px,3vw,33px); line-height:1.15; margin:8px 0 5px }} .label {{ color:var(--muted); font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:.06em }}
.card small {{ color:var(--muted) }} .ok {{ color:var(--teal) }} .warn {{ color:var(--coral) }}
.split {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-top:20px }} .panel p:last-child {{ margin-bottom:0 }}
.chart {{ display:block; width:100%; height:auto; border:1px solid var(--line); border-radius:10px; background:white; margin:19px 0 8px }}
.table-wrap {{ overflow-x:auto; background:white; border:1px solid var(--line); border-radius:12px; margin-top:18px }} table {{ border-collapse:collapse; width:100%; font-size:14px }}
th,td {{ padding:12px 13px; border-bottom:1px solid var(--line); text-align:right; white-space:nowrap }} th:first-child,td:first-child {{ text-align:left }} thead {{ background:#e9f4f3 }} tbody tr:last-child th,tbody tr:last-child td {{ border-bottom:0 }}
a {{ color:var(--teal); text-decoration:underline; text-underline-offset:3px }} a:hover {{ color:var(--coral) }}
ul {{ margin:10px 0 0; padding-left:22px }} li {{ margin:7px 0 }} .callout {{ border-left:5px solid var(--coral); background:#fff5ed; padding:18px 22px; border-radius:0 10px 10px 0; margin-top:22px }}
.foot {{ border-top:1px solid var(--line); margin-top:55px; padding-top:20px; font-size:13px; color:var(--muted) }}
@media(max-width:800px) {{ .grid {{ grid-template-columns:repeat(2,1fr) }} .split {{ grid-template-columns:1fr }} }}
@media(max-width:520px) {{ .page {{ padding-left:18px; padding-right:18px }} .grid {{ grid-template-columns:1fr }} }}
@media print {{
  @page {{ size:A4 landscape; margin:12mm }}
  body {{ background:white; font-size:12px }} header {{ padding:20px 0; print-color-adjust:exact }}
  header h1 {{ font-size:34px }} header p {{ font-size:14px }} .meta {{ margin-top:10px }}
  .page {{ max-width:none; padding-left:0; padding-right:0 }} section {{ margin-top:25px; break-inside:auto }}
  h2 {{ font-size:23px }} .card,.panel {{ box-shadow:none; padding:12px }} .card strong {{ font-size:25px }}
  th,td {{ font-size:10px; padding:6px 5px }} .table-wrap {{ overflow:visible }} .chart {{ max-width:700px; margin:10px auto }}
  .callout {{ padding:10px 14px }} .foot {{ margin-top:25px }}
}}
</style></head><body>
<header><div class="page"><div class="eyebrow">Victor Marino · Game QA portfolio</div><h1>Game QA Evidence Report</h1>
<p>What does this small slot game promise, and what did the checks actually observe?</p>
<div class="meta">Generated {timestamp} · {n:,} seeded research spins · seed {metrics['seed']} · 3 reels · {config.reel_length} stops per reel</div></div></header>
<main class="page">
<section><h2>The result in one glance</h2><p class="lead">Return to player (RTP) means winnings divided by total staked. It is a long-run model average, not what any one player receives.</p>
<div class="grid">
<div class="card"><span class="label">Expected RTP</span><strong>{metrics['theory']*100:.4f}%</strong><small>Calculated from reel weights and prizes</small></div>
<div class="card"><span class="label">Observed RTP</span><strong>{metrics['observed']*100:.4f}%</strong><small>{n:,} repeatable spins</small></div>
<div class="card"><span class="label">Gap</span><strong>{metrics['difference_pp']:.4f} pp</strong><small>Absolute percentage-point difference</small></div>
<div class="card"><span class="label">Automated tests</span><strong class="{test_class}">{tests['passed']}/{tests['tests']}</strong><small>{escape(tests['status'])}; {tests['failed']} failed, {tests['skipped']} skipped</small></div>
</div><div class="split">
<div class="panel"><h3>How often did a win occur?</h3><p><strong>{metrics['observed_hit']*100:.3f}% observed</strong> versus {metrics['theoretical_hit']*100:.3f}% expected. A win means three matching symbols.</p><p>{metrics['wins']:,} winning spins; {n-metrics['wins']:,} losing spins.</p></div>
<div class="panel"><h3>What happened to the stakes?</h3><p>{result['total_bet']:,.0f} credits staked; {result['total_win']:,.0f} credits paid out in this run.</p><p>The theoretical house edge for this simple paytable is {(1-metrics['theory'])*100:.4f}%.</p></div>
</div><div class="callout"><strong>Read the result carefully.</strong> A model-based 95% reference range for a run of this size is {metrics['band_low']*100:.3f}%–{metrics['band_high']*100:.3f}%. The observed result is {'inside' if metrics['in_band'] else 'outside'} that range. This range assumes independent spins under the stated model. It is a diagnostic, not a certification decision.</div>
</section>
<section><h2>Does the long run approach the math?</h2><p class="lead">The line uses a logarithmic spin axis so early swings remain visible. The red reference is the calculated RTP.</p>
<img class="chart" src="data:image/png;base64,{inline_png(convergence_png)}" alt="Cumulative observed RTP by spin count compared with theoretical RTP">
<p class="lead">The seeded NumPy simulator makes this experiment repeatable. Normal unseeded spins use an OS-backed <code>SystemRandom</code> through a separate path.</p></section>
<section><h2>What do the reels and prizes say?</h2><p class="lead">Each of the three reels uses the same 20-stop weighting. Only three matching symbols pay. “Win spins” count complete three-reel matches; “draw share” counts each individual reel position.</p>
<div class="table-wrap"><table><thead><tr><th>Symbol</th><th>Stops</th><th>Expected draw share</th><th>Observed draw share</th><th>Expected win spins</th><th>Observed win spins</th><th>Prize</th><th>Expected RTP part</th><th>Observed RTP part</th></tr></thead><tbody>{''.join(table_rows)}</tbody></table></div>
<p class="lead" style="margin-top:14px">Expected RTP = sum of (symbol probability³ × payout multiplier) ÷ stake. The five “RTP part” values add up to the overall result.</p>
<img class="chart" src="data:image/png;base64,{inline_png(frequency_png)}" alt="Expected and observed symbol frequencies for the five symbols"></section>
<section><h2>Are the symbol counts plausible?</h2><div class="split"><div class="panel"><h3 class="{'ok' if metrics['frequency_ok'] else 'warn'}">{frequency_label}</h3><p>Chi-square statistic: <strong>{metrics['chi2']:.3f}</strong><br>p-value: <strong>{p_value}</strong><br>Decision threshold: <strong>0.05</strong></p></div>
<div class="panel"><h3>What this check means</h3><p>The observed symbol totals were compared with the expected 6:5:4:3:2 ratio. {'This sample did not show a statistically significant frequency mismatch.' if metrics['frequency_ok'] else 'This sample showed a statistically significant frequency mismatch.'}</p><p>A passing frequency check cannot prove independence or unpredictability.</p></div></div></section>
<section><h2>Which quality rules have tests?</h2><p class="lead">These counts come from the test runner’s XML result, not from the simulation. Open a test file to see its inputs and assertions.</p>
<div class="split"><div class="panel"><h3>Test run: <span class="{test_class}">{escape(tests['status'])}</span></h3><p>{escape(tests['detail'])} {tests['passed']} passed, {tests['failed']} failed, {tests['skipped']} skipped.</p><ul><li>Exact payouts and invalid inputs</li><li>Wallet balances, concurrent bets and loss limits</li><li>RTP, distribution checks and RNG predictability demonstration</li></ul></div>
<div class="table-wrap" style="margin-top:0"><table><thead><tr><th>Test file</th><th>Cases</th></tr></thead><tbody>{test_rows}</tbody></table></div></div></section>
<section><h2>What this report does not prove</h2><div class="split"><div class="panel"><h3>Model boundaries</h3><ul><li>This is a portfolio slot model, not a deployed or certified game.</li><li>The wallet is in memory. A real-money system needs durable transactions and payout recovery.</li><li>The session limit is net loss from the starting balance, not a time-scoped regulatory control.</li></ul></div>
<div class="panel"><h3>Randomness boundaries</h3><ul><li>The seeded simulation is for repeatable research. It does not exercise the secure normal spin path millions of times.</li><li>The chi-square check examines overall symbol frequencies; other patterns may remain.</li><li>The MT19937 attack demonstration assumes access to 624 raw 32-bit outputs, which ordinary players normally cannot see.</li></ul></div></div></section>
<div class="foot">How to reproduce: <code>python run_simulation.py</code> from the project root after installing requirements. The report and charts are saved in <code>reports/</code>. Explore the <a href="{repo}/blob/master/README.md">README</a>, <a href="{repo}/blob/master/src/slot_engine.py">game rules</a>, <a href="{repo}/blob/master/src/wallet.py">wallet</a>, <a href="{repo}/blob/master/src/rng_audit.py">frequency audit</a>, and <a href="{repo}/blob/master/.github/workflows/ci.yml">CI workflow</a>.</div>
</main></body></html>"""
