import sqlite3
db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
# Use single quotes for inner string, double quotes for outer
cursor.execute("SELECT title, path FROM media WHERE title LIKE '%Пуаро%' ORDER BY path")
results = cursor.fetchall()
for row in results:
    print(row)
conn.close()
