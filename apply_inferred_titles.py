import sqlite3
import csv

db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

updated_count = 0

with open("inferred_titles_report.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rec_id = row["ID"]
        inferred_title = row["Inferred Title_ru"]
        
        if inferred_title != "COULD_NOT_INFER":
            cursor.execute("UPDATE media SET title_ru = ? WHERE id = ?", (inferred_title, rec_id))
            updated_count += 1

conn.commit()
print(f"Updated {updated_count} records in the database.")
conn.close()
