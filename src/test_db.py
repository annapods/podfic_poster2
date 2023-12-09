import sqlite3


con = sqlite3.connect("podfics.db")
cur = con.cursor()
table = "table1"

cur.execute(f"DROP TABLE IF EXISTS {table}")  # TODO not secure
cur.execute(f"CREATE TABLE {table}(ID, field1, field2, field3)")
res = cur.execute("SELECT name FROM sqlite_master")
res.fetchone()

data = [
    (1, "test1", 1, ""),
    (2, "test2", 2, ""),
]
cur.executemany(f"INSERT INTO {table} VALUES(?, ?, ?, ?)", data)
con.commit()
res = cur.execute(f"SELECT * FROM {table}")
data = res.fetchall()

