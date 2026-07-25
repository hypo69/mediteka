import sqlite3

db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('SELECT id, path, title FROM media WHERE title_ru IS NULL OR title_ru = ""')
rows = cursor.fetchall()
print(f"Remaining records: {len(rows)}")
for row in rows[:50]: # Print first 50 to see what's left
    print(row)
conn.close()
