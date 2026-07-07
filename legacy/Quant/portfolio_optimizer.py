import pandas as pd
import numpy as np
import sqlite3
from scipy.optimize import minimize

RESULTS_DB_PATH = "quant.db"

def get_strategy_returns():
    """Fetches total returns of all strategies from quant.db."""
    conn = sqlite3.connect(RESULTS_DB_PATH)
    query = "SELECT ticker, strategy, total_return / 100.0 AS total_return FROM strategy_results"
    df = pd.read_sql(query, conn)
    conn.close()
    
    df = df.pivot(index="ticker", columns="strategy", values="total_return")
    df.dropna(inplace=True)
    return df

def sharpe_ratio(weights, returns):
    """Calculates Sharpe ratio for a given portfolio allocation."""
    portfolio_return = np.dot(weights, returns.mean())
    portfolio_std = np.sqrt(np.dot(weights.T, np.dot(returns.cov(), weights)))
    return -portfolio_return / portfolio_std  # Negative for minimization

def optimize_portfolio():
    """Finds the optimal allocation to maximize Sharpe ratio."""
    returns = get_strategy_returns()
    num_strategies = returns.shape[1]
    init_weights = np.ones(num_strategies) / num_strategies
    bounds = [(0, 1)] * num_strategies
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

    result = minimize(sharpe_ratio, init_weights, args=(returns,), method="SLSQP", bounds=bounds, constraints=constraints)
    return result.x, returns.columns

weights, strategies = optimize_portfolio()

print("📊 Optimized Portfolio Weights:")
for strat, weight in zip(strategies, weights):
    print(f"{strat}: {weight:.2%}")
