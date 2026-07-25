import sqlite3

db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check for empty title_ru
cursor.execute("SELECT id, path, title, title_orig FROM media WHERE title_ru IS NULL OR title_ru = ''")
rows = cursor.fetchall()
with open("empty_title_ru_list.txt", "w", encoding="utf-8") as f:
    for row in rows:
        f.write(str(row) + "\n")

print(f"Wrote {len(rows)} records to empty_title_ru_list.txt")

conn.close()
