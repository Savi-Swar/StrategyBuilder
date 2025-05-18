import sqlite3

DB_PATH = "quant.db"

def reset_results_table():
    """Clears all data from the strategy_results table but keeps the structure intact."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Delete all existing records
    cursor.execute("DELETE FROM strategy_results;")
    
    # Reset the auto-increment ID counter
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='strategy_results';")

    conn.commit()
    conn.close()
    print("🧹 `strategy_results` table cleared! All sample data removed.")

if __name__ == "__main__":
    reset_results_table()
