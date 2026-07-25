import sqlite3

# Mapping: Brooklyn 9-9 (4855-4874), The Wire (6047-6074), The Americans (6075-6076)
mapping = {
    **{str(i): "Бруклин 9-9" for i in range(4855, 4875)},
    **{str(i): "Прослушка" for i in range(6047, 6075)},
    "6075": "Американцы", "6076": "Американцы"
}

db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for rec_id, title_ru in mapping.items():
    cursor.execute("UPDATE media SET title_ru = ? WHERE id = ?", (title_ru, rec_id))

conn.commit()
print(f"Updated {len(mapping)} records in the database.")
conn.close()
