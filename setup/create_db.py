import sqlite3

def create_database():
    # Connect to (or create) the database file
    conn = sqlite3.connect('stocks.db')
    cursor = conn.cursor()

    # Enable foreign key support (just in case)
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Create the table for storing stock price data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        date TEXT NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER
    );
    ''')
    
    # Commit changes and close the connection
    conn.commit()
    conn.close()
    print("✅ Database and 'stocks' table created successfully!")

if __name__ == '__main__':
    create_database()
