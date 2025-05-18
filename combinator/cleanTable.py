import sqlite3

DB_PATH = "quant.db"
TABLE_NAME = "daily_returns_table"

def clean_daily_returns_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?;
    """, (TABLE_NAME,))
    exists = cursor.fetchone()

    if not exists:
        print(f"⚠️ Table '{TABLE_NAME}' does not exist in {DB_PATH}. Nothing to clean.")
        conn.close()
        return

    # Delete all data
    cursor.execute(f"DELETE FROM {TABLE_NAME}")
    conn.commit()

    # Confirm deletion
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        print(f"🧼 Successfully cleaned all rows from '{TABLE_NAME}'.")
    else:
        print(f"❌ Something went wrong — {count} rows still present.")

if __name__ == "__main__":
    clean_daily_returns_table()
