import sqlite3
import pandas as pd

DB_PATH = "Quark.db"

def clean_duplicate_prices():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all tickers
    tickers = pd.read_sql("SELECT DISTINCT ticker FROM stocks", conn)["ticker"].tolist()

    for ticker in tickers:
        print(f"🧹 Cleaning {ticker}...")

        # Load all data for ticker
        df = pd.read_sql("SELECT * FROM stocks WHERE ticker = ?", conn, params=(ticker,))
        df["date"] = pd.to_datetime(df["date"])

        # Drop duplicate dates, keeping last
        df = df.sort_values("date").drop_duplicates(subset=["date"], keep="last")

        # Delete old data
        cursor.execute("DELETE FROM stocks WHERE ticker = ?", (ticker,))
        conn.commit()

        # Re-insert cleaned data
        df.to_sql("stocks", conn, if_exists="append", index=False)

    conn.close()
    print("✅ Done cleaning Quark.db!")

if __name__ == "__main__":
    clean_duplicate_prices()
