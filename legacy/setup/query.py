import sqlite3

# ✅ Connect to SQLite database
conn = sqlite3.connect("Quark.db")
cursor = conn.cursor()

# ✅ Query the first 10 rows from 'stocks' table
cursor.execute("SELECT * FROM stocks LIMIT 10;")
rows = cursor.fetchall()

# ✅ Display results
print("\n📊 First 10 rows from 'stocks' table:\n")
for row in rows:
    print(row)

# ✅ Close database connection
conn.close()
