import sqlite3
db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
# Use single quotes for path string
cursor.execute("DELETE FROM media WHERE path IS NULL OR path = ''")
print(f"Удалено записей: {cursor.rowcount}")
conn.commit()
conn.close()
