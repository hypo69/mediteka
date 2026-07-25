import sqlite3

db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Update for Otverzhennye
cursor.execute("UPDATE media SET title_ru = ? WHERE id = ?", ('Отверженные (2012)', 6284))
conn.commit()

print(f"Updated record 6284: title_ru = 'Отверженные (2012)'")

conn.close()
