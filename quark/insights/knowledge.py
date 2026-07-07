"""Vig's knowledge base: everything the research produced, assembled into a
dossier the commentary model is grounded in. This is how the agent gets
"trained" — not by changing weights, but by giving it the desk's actual
evidence base and rules for reasoning from it."""

import pandas as pd

from quark import config

ROOT = config.ROOT


def _csv_block(name: str, path, max_rows: int = 20) -> str:
    try:
        df = pd.read_csv(path)
        return f"### {name}\n{df.head(max_rows).to_string(index=False)}\n"
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return ""


def _notes_block(max_chars: int = 6000) -> str:
    try:
        text = (ROOT / "RESEARCH_NOTES.md").read_text()[:max_chars]
        return f"### Research notes (decision log, verbatim)\n{text}\n"
    except FileNotFoundError:
        return ""


def build_dossier(health: dict | None = None) -> str:
    """The full evidence base, assembled fresh each run."""
    parts = [
        "## VIG RESEARCH DOSSIER — the only evidence you may cite\n",
        _csv_block("Classic baselines, net of costs (full period)",
                   config.REPORTS_DIR / "baselines.csv"),
        _csv_block("Study 1 ML timing results (OOS 2012+)",
                   config.REPORTS_DIR / "ml_results.csv"),
        _csv_block("Study 2 cross-sectional results (OOS 2012+)",
                   config.REPORTS_DIR / "xsec_results.csv"),
        _csv_block("Study 2 per-fold AUC/base-rate",
                   config.REPORTS_DIR / "xsec_fold_stats.csv"),
        _csv_block("Live + walk-forward IC ledger (most recent last)",
                   config.REPORTS_DIR / "ledger" / "ic_history.csv",
                   max_rows=30),
        _notes_block(),
    ]
    if health:
        parts.append(
            "### Current model health\n"
            f"status={health.get('model_status')} | {health.get('model_detail')} | "
            f"data {health.get('data_age_bdays')} business days old\n"
        )
    return "\n".join(p for p in parts if p)
