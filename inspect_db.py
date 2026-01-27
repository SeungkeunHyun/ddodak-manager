import duckdb
try:
    con = duckdb.connect('ddodak.duckdb')
    print("Members Area Sample:")
    print(con.execute("SELECT area, count(*) as cnt FROM members GROUP BY area ORDER BY cnt DESC LIMIT 20").df())
    print("\nMembers Description Sample (for address):")
    print(con.execute("SELECT description FROM members WHERE description IS NOT NULL LIMIT 5").df())
except Exception as e:
    print(e)
