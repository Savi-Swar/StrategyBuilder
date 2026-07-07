import sqlite3

def deduplicate_strategy_results(db_path="quant.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Delete older duplicates based on (ticker, strategy) keeping the one with max id
    cursor.execute("""
        DELETE FROM strategy_results
        WHERE id NOT IN (
            SELECT MAX(id) FROM strategy_results
            GROUP BY ticker, strategy
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Cleaned duplicates from strategy_results.")

if __name__ == "__main__":
    deduplicate_strategy_results()
