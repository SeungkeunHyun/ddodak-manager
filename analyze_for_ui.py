import duckdb
import pandas as pd
import os

db_path = r"d:/myCoding/python/band/ddodak/docker/ddodak.duckdb"

if not os.path.exists(db_path):
    print("DB not found")
    exit()

with duckdb.connect(db_path) as conn:
    print("--- AREAS ---")
    print(conn.execute("SELECT area, COUNT(*) as cnt FROM members GROUP BY area ORDER BY cnt DESC LIMIT 10").df())
    
    print("\n--- ROLES ---")
    print(conn.execute("SELECT role, COUNT(*) as cnt FROM members GROUP BY role").df())
    
    print("\n--- EVENT TREND ---")
    try:
        # DuckDB string format for date might vary, trying standard
        print(conn.execute("SELECT strftime(date, '%Y-%m') as month, COUNT(*) as cnt FROM events GROUP BY month ORDER BY month DESC LIMIT 6").df())
    except:
        print("Date convert failed, showing raw dates")
        print(conn.execute("SELECT date FROM events LIMIT 5").df())
