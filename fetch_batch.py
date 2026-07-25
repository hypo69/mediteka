import sqlite3

db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('SELECT id, path, title FROM media WHERE title_ru IS NULL OR title_ru = "" LIMIT 20')
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
