import duckdb
con = duckdb.connect('ddodak.duckdb')
print("--- Views ---")
views = con.execute("SELECT name, sql FROM sqlite_master WHERE type='view'").df()
for _, row in views.iterrows():
    print(f"View: {row['name']}")
    print(row['sql'])
    print("-" * 20)

print("\n--- Tables ---")
tables = con.execute("SELECT name, sql FROM sqlite_master WHERE type='table'").df()
for _, row in tables.iterrows():
    print(f"Table: {row['name']}")
    print(row['sql'])
    print("-" * 20)
