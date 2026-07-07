import pandas as pd
from algos.GoldenCross import golden_cross_strategy  # Import Golden Cross strategy

# ✅ List of stocks to test
TICKERS = ["MSFT", "NVDA", "META", "GOOGL", "^GSPC", "^DJI", "BTC-USD"]

def run_golden_cross():
    """Runs Golden Cross for all tickers and collects daily returns."""
    combined_df = pd.DataFrame()  # Empty DataFrame to store all returns

    for ticker in TICKERS:
        print(f"🔄 Running Golden Cross for {ticker}...")
        daily_returns = golden_cross_strategy(ticker)  # Get daily PnL DataFrame
        
        if daily_returns is not None:
            if combined_df.empty:
                combined_df = daily_returns  # First stock, initialize DataFrame
            else:
                combined_df = combined_df.join(daily_returns, how="outer")  # Merge stocks

    # ✅ Display combined daily returns (PnL)
    print("\n📊 Combined Daily Returns (First 5 rows):")
    print(combined_df.head())

    return combined_df  # Return for further portfolio analysis

# ✅ Run the strategy runner
if __name__ == "__main__":
    portfolio_returns = run_golden_cross()
