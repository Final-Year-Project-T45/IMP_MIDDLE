import sqlite3

for db_path in ["finsecure.db", "backend/finsecure.db"]:
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("UPDATE accounts SET status = 'ACTIVE', balance = 250000.0 WHERE account_id LIKE '%4821'")
        cur.execute("UPDATE accounts SET status = 'ACTIVE' WHERE account_id LIKE '%9034'")
        cur.execute("UPDATE accounts SET status = 'ACTIVE' WHERE account_id LIKE '%7742'")
        conn.commit()
        cur.execute("SELECT account_id, status, balance FROM accounts")
        rows = cur.fetchall()
        print(f"{db_path} accounts:")
        for r in rows:
            print(f"  {r}")
        conn.close()
    except Exception as e:
        print(f"Error updating {db_path}: {e}")
