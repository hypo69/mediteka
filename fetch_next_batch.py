import sqlite3

db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
# Offset 20 because we already did the first 20
cursor.execute('SELECT id, path, title FROM media WHERE title_ru IS NULL OR title_ru = "" LIMIT 50 OFFSET 20')
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
