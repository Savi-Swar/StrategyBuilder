"""One-page research summary PDF — the thing you hand an interviewer.

Reads only committed report CSVs (no DB needed), so it regenerates anywhere:
    python scripts/make_onepager.py  ->  reports/quark_onepager.pdf
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from quark import config  # noqa: E402

R = config.REPORTS_DIR
INK, DIM, ACC, RED = "#1a1d21", "#6b7280", "#0d7a5f", "#b3402e"


def main() -> None:
    xsec = pd.read_csv(R / "xsec_results.csv", index_col=0)
    deciles = pd.read_csv(R / "xsec_decile_means.csv", index_col=0)["fwd"]
    ic = pd.read_csv(R / "xsec_ic_series.csv", index_col=0,
                     parse_dates=True).iloc[:, 0]
    ls = pd.read_csv(R / "xsec_daily_returns.csv", index_col=0,
                     parse_dates=True).iloc[:, 0]
    base = pd.read_csv(R / "baselines.csv", index_col=0)
    ic_t = float(ic.mean() / ic.std() * np.sqrt(len(ic)))

    fig = plt.figure(figsize=(8.5, 11))
    fig.subplots_adjust(left=0.09, right=0.95, top=0.90, bottom=0.05,
                        hspace=0.65)

    fig.text(0.09, 0.965, "Quark — systematic trading research, done honestly",
             size=16, weight="bold", color=INK)
    fig.text(0.09, 0.945,
             "Savitur Swarup · github.com/Savi-Swar/StrategyBuilder\n"
             "all results out-of-sample 2012+, net of costs, purged "
             "walk-forward, deflated for trial count",
             size=8, color=DIM, va="top", linespacing=1.5)

    fig.text(0.09, 0.902, "Headline finding", size=11, weight="bold", color=INK)
    band = None
    band_path = R / "turnover_study.csv"
    if band_path.exists():
        band = pd.read_csv(band_path, index_col=0)
    band_line = ""
    if band is not None and "band_exit_30" in band.index:
        band_line = ("\na pre-registered no-trade band (hold until rank "
                     "decays 0.30) lifts it to "
                     f"{band.loc['band_exit_30', 'sharpe']:.2f} at half the "
                     "cost drag.")
    fig.text(0.09, 0.888,
             "A gradient-boosted cross-sectional model over ~500 S&P 500 "
             "stocks predicts next-week relative\nreturns: weekly rank IC = "
             f"{ic.mean():+.4f} (t = {ic_t:.2f}, n = {len(ic)} "
             "non-overlapping weeks), near-monotonic decile\nspread. "
             "Economics are thin after costs — the honest headline is "
             "predictive power, not easy money:\nnet Sharpe "
             f"{xsec.loc['ls_weekly_h5_net', 'sharpe']:.2f} weekly, "
             f"{xsec.loc['ls_monthly_h21_net', 'sharpe']:.2f} monthly;"
             f"{band_line}\nControls: shuffled-label AUC 0.500 / IC ≈ 0; "
             "the long side carries the signal (shorting did not pay).",
             size=8.5, color=INK, va="top", linespacing=1.6)

    # Panel 1: decile spread
    ax1 = fig.add_axes([0.09, 0.575, 0.39, 0.19])
    colors = [RED if d <= 3 else DIM if d <= 7 else ACC for d in deciles.index]
    ax1.bar(deciles.index, deciles.values * 1e4, color=colors, width=0.75)
    ax1.set_title("Gross fwd 5d return by prediction decile (bps)",
                  size=8.5, color=INK, loc="left")
    ax1.set_xticks(range(1, 11))

    # Panel 2: rolling IC
    ax2 = fig.add_axes([0.56, 0.575, 0.39, 0.19])
    roll = ic.rolling(26).mean()
    ax2.plot(roll.index, roll.values, color=ACC, lw=1.2)
    ax2.axhline(0, color=DIM, lw=0.6)
    ax2.set_title("26-week rolling mean IC (weekly, Spearman)",
                  size=8.5, color=INK, loc="left")

    # Panel 3: equity curves
    ax3 = fig.add_axes([0.09, 0.315, 0.86, 0.18])
    eq = (1 + ls).cumprod()
    ax3.plot(eq.index, eq.values, color=INK, lw=1.1,
             label="L/S weekly, net (flagship)")
    ax3.axhline(1, color=DIM, lw=0.6)
    ax3.legend(frameon=False, fontsize=7.5, loc="upper left")
    ax3.set_title("Dollar-neutral extreme-decile long/short — "
                  "net equity curve", size=8.5, color=INK, loc="left")

    for ax in (ax1, ax2, ax3):
        ax.tick_params(labelsize=7, colors=DIM)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(DIM)

    # Honest failures + method table. Benchmarks are not strategy trials —
    # exclude them before naming the best classic variant.
    strat = base[~base.index.str.contains("buy_hold|GSPC|_lag2|_with_stocks")]
    best = strat["sharpe"].idxmax()
    fig.text(0.09, 0.285, "What failed, reported anyway", size=11,
             weight="bold", color=INK)
    fig.text(0.09, 0.262,
             f"Classic indicators (8 counted variants): best = {best}, "
             "Deflated Sharpe Ratio 0.19 — the best of 8\ncoin flips. Daily "
             "ML timing on 43 multi-asset instruments: AUC 0.518 does not "
             "clear costs\n(net Sharpe −0.44, DSR ≈ 0). Stated limits: "
             "survivorship-biased equity universe (current members),\n"
             "non-back-adjusted futures, price-only index benchmark.",
             size=8.5, color=INK, va="top", linespacing=1.6)

    fig.text(0.09, 0.160, "Why the numbers can be trusted", size=11,
             weight="bold", color=INK)
    defenses = [
        ("Lookahead", "positions = signal.shift(lag), lag ≥ 1 enforced; "
                      "unit test: prescient signal earns exactly zero"),
        ("Leakage", "purged + embargoed walk-forward (purge ≥ horizon); "
                    "shuffled-label control run for every ML study"),
        ("Costs", "per-asset-class bps on turnover, entry bar charged; "
                  "a missing cost rate raises, never defaults to free"),
        ("Selection", "every variant in a counted registry; best-of-family "
                      "Sharpe deflated (Bailey & López de Prado DSR)"),
        ("Verification", "64 unit tests on synthetic fixtures; independent "
                         "cross-source price verification in the daily job"),
    ]
    y = 0.138
    for name, desc in defenses:
        fig.text(0.09, y, name, size=8, weight="bold", color=ACC)
        fig.text(0.24, y, desc, size=8, color=INK)
        y -= 0.022

    fig.text(0.09, 0.040,
             "Ships as “Vig”: a serverless self-grading terminal — every "
             "prediction logged to a ledger and scored after its\nhorizon "
             "completes; a live trust gate turns the desk off when the "
             "trailing IC decays.",
             size=8, color=DIM, style="italic", va="top", linespacing=1.5)

    out = R / "quark_onepager.pdf"
    fig.savefig(out, format="pdf")
    print("wrote", out)


if __name__ == "__main__":
    main()
