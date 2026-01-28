import duckdb
import os
import sys

db_path = r"d:/myCoding/python/band/ddodak/docker/ddodak.duckdb"

print(f"Checking DB at: {db_path}")
if not os.path.exists(db_path):
    print("DB file not found!")
    sys.exit(1)

try:
    with duckdb.connect(db_path) as conn:
        df = conn.execute("SELECT gender, COUNT(*) as count FROM members GROUP BY gender").df()
        print(df)
except Exception as e:
    print(f"Error: {e}")
