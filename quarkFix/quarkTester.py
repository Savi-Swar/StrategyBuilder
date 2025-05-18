import sqlite3
import pandas as pd

DB_PATH = "Quark.db"

def inspect_duplicates():
    conn = sqlite3.connect(DB_PATH)

    # Load all data
    df = pd.read_sql("SELECT ticker, date FROM stocks", conn)
    conn.close()

    # Convert date to datetime
    df["date"] = pd.to_datetime(df["date"])

    # Count duplicates
    dupes = (
        df.groupby(["ticker", "date"])
        .size()
        .reset_index(name="count")
        .query("count > 1")
        .sort_values(["ticker", "date"])
    )

    if dupes.empty:
        print("✅ No duplicate (ticker, date) pairs found.")
    else:
        print(f"❗ Found {len(dupes)} duplicated (ticker, date) rows:\n")
        for ticker in dupes["ticker"].unique():
            sub = dupes[dupes["ticker"] == ticker]
            print(f"📊 {ticker} — {len(sub)} duplicates")
            print(sub.head(5).to_string(index=False))  # Show first 5 for preview
            print()

if __name__ == "__main__":
    inspect_duplicates()
