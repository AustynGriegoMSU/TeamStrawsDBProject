## Connect DB
import turso

con = turso.connect("sqlite.db")
cur = con.cursor()

## QUERY DB
res = cur.execute("SELECT * FROM users")
users = res.fetchall()
print(users)