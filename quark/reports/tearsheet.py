"""One-figure tearsheet: equity vs benchmark, drawdown, rolling Sharpe,
monthly heatmap, plus an optional study-specific panel."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from quark import config


def _drawdown(returns: pd.Series) -> pd.Series:
    eq = (1 + returns.fillna(0)).cumprod()
    return eq / eq.cummax() - 1.0


def make_tearsheet(
    portfolio: pd.Series,
    benchmark: pd.Series | None,
    title: str,
    out_path,
    extra_panel: tuple[str, pd.Series] | None = None,
) -> None:
    fig = plt.figure(figsize=(13, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.45, wspace=0.25)
    fig.suptitle(title, fontsize=14, fontweight="bold")

    ax = fig.add_subplot(gs[0, :])
    (1 + portfolio.fillna(0)).cumprod().plot(ax=ax, label="strategy (net)", lw=1.2)
    if benchmark is not None:
        (1 + benchmark.reindex(portfolio.index).fillna(0)).cumprod().plot(
            ax=ax, label="S&P 500 (price index)", lw=1.0, alpha=0.8)
    ax.set_yscale("log")
    ax.set_title("Cumulative growth of $1 (log scale)")
    ax.legend()
    ax.grid(alpha=0.3)

    ax = fig.add_subplot(gs[1, 0])
    _drawdown(portfolio).plot(ax=ax, color="crimson", lw=0.9)
    ax.set_title("Drawdown")
    ax.grid(alpha=0.3)

    ax = fig.add_subplot(gs[1, 1])
    roll = (
        portfolio.rolling(252).mean() / portfolio.rolling(252).std()
        * np.sqrt(config.ANN_FACTOR)
    )
    roll.plot(ax=ax, lw=0.9)
    ax.axhline(0, color="gray", ls="--", lw=0.7)
    ax.set_title("Rolling 1y Sharpe")
    ax.grid(alpha=0.3)

    ax = fig.add_subplot(gs[2, 0])
    monthly = portfolio.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    pivot = pd.DataFrame(
        {"year": monthly.index.year, "month": monthly.index.month, "ret": monthly.values}
    ).pivot(index="year", columns="month", values="ret")
    im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn",
                   vmin=-np.nanmax(np.abs(pivot.values)),
                   vmax=np.nanmax(np.abs(pivot.values)))
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    ax.set_xticks(range(12), ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    ax.set_title("Monthly returns")
    fig.colorbar(im, ax=ax, fraction=0.04)

    ax = fig.add_subplot(gs[2, 1])
    if extra_panel is not None:
        name, series = extra_panel
        if isinstance(series.index, pd.DatetimeIndex):
            series.cumsum().plot(ax=ax, lw=0.9)
        else:
            series.plot.bar(ax=ax, color="steelblue")
        ax.set_title(name)
    else:
        ax.axis("off")
    ax.grid(alpha=0.3)

    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
