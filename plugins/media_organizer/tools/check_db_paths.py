import sqlite3
db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
# Use single quotes for inner string, double quotes for outer
cursor.execute("SELECT path FROM media WHERE path LIKE '%Poirot%' AND path LIKE '%.m4v' LIMIT 5")
print(cursor.fetchall())
conn.close()
