import sqlite3

db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM media WHERE title_ru IS NULL OR title_ru = ""')
count = cursor.fetchone()[0]
print(f"Remaining records: {count}")
conn.close()
