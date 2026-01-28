import duckdb
import pandas as pd

try:
    with duckdb.connect('ddodak.duckdb') as conn:
        print("--- TABLES ---")
        print(conn.execute("SHOW TABLES").df())
        
        print("\n--- VIEW: v_member_attendance_summary ---")
        try:
            print(conn.execute("DESCRIBE v_member_attendance_summary").df())
            print(conn.execute("SELECT * FROM v_member_attendance_summary LIMIT 1").df())
        except Exception as e:
            print(f"Error describing view: {e}")
            
        print("\n--- TABLE: members ---")
        try:
            print(conn.execute("DESCRIBE members").df())
        except: pass

        print("\n--- TABLE: events ---")
        try:
            print(conn.execute("DESCRIBE events").df())
        except: pass
        
        print("\n--- TABLE: feeds (if exists) ---")
        try:
            print(conn.execute("DESCRIBE feeds").df())
        except: 
            print("No 'feeds' table found.")

except Exception as e:
    print(f"DB Error: {e}")
