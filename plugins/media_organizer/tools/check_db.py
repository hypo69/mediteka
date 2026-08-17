import sqlite3
db = 'plugins/media_organizer/data/media.db'
conn = sqlite3.connect(db)
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables:', tables)
for t in tables:
    info = conn.execute(f"PRAGMA table_info({t[0]})").fetchall()
    print(f'{t[0]} columns:', [r[1] for r in info])
conn.close()
