"""Build tearsheets and the README results table from the saved run outputs.
Consumes reports/*.csv written by run_baselines.py / run_ml.py / run_xsec.py,
so every published number is regenerable from the two run scripts."""

import pandas as pd

from quark import config
from quark.data.loader import compute_returns, load_prices
from quark.reports.tables import comparison_table, to_markdown
from quark.reports.tearsheet import make_tearsheet

R = config.REPORTS_DIR


def main() -> None:
    gspc = compute_returns(load_prices(tickers=["^GSPC"]))["^GSPC"]

    ml = pd.read_csv(R / "ml_daily_returns.csv", index_col=0, parse_dates=True)
    xsec = pd.read_csv(R / "xsec_daily_returns.csv", index_col=0,
                       parse_dates=True).iloc[:, 0]
    deciles = pd.read_csv(R / "xsec_decile_means.csv", index_col=0).iloc[:, 0]

    make_tearsheet(
        xsec, gspc,
        "Study 2 — Cross-sectional L/S equity (weekly deciles, net of costs)",
        R / "study2_tearsheet.png",
        extra_panel=("Gross 5d fwd return by prediction decile", deciles * 1e4),
    )
    make_tearsheet(
        ml["tsmom_252"], gspc,
        "Study 1 — Multi-asset tsmom_252 (vol-targeted, net of costs)",
        R / "study1_tearsheet.png",
        extra_panel=("ML timing model (net, same window)", ml["ml"]),
    )

    table = comparison_table(
        {
            "xsec_ls_weekly (S2)": xsec,
            "ml_timing (S1)": ml["ml"],
            "tsmom_252 (S1)": ml["tsmom_252"],
            "buy&hold ^GSPC": gspc.loc[xsec.index.min():],
        }
    )
    md = to_markdown(table)
    (R / "results_table.md").write_text(md + "\n")
    print(md)
    print(f"\nWrote {R / 'study1_tearsheet.png'}, {R / 'study2_tearsheet.png'}, "
          f"{R / 'results_table.md'}")


if __name__ == "__main__":
    main()
