import sqlite3

conn = sqlite3.connect(r'C:\mediateka\plugins\media_organizer\data\media.db')
cursor = conn.cursor()

# Query for the film
query = "SELECT id, title_ru, disk_name, path FROM media WHERE title_ru LIKE ?"
cursor.execute(query, ('%Бабушка лёгкого поведения%',))
results = cursor.fetchall()

print('Results:', results)

conn.close()
