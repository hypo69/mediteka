import sqlite3
import json

db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'

# Mapping provided in the previous turn
mapping = {
  "772": "Пианистка",
  "773": "Полночь в Париже",
  "948": "Дом Gucci",
  "1130": "Кунг-фу жеребец",
  "1131": "Операция «Панда»",
  "4507": "Благочестивая Марта",
  "4841": "Бруклин 9-9",
  "4842": "Бруклин 9-9",
  "4843": "Бруклин 9-9",
  "4844": "Бруклин 9-9",
  "4845": "Бруклин 9-9",
  "4846": "Бруклин 9-9",
  "4847": "Бруклин 9-9",
  "4848": "Бруклин 9-9",
  "4849": "Бруклин 9-9",
  "4850": "Бруклин 9-9",
  "4851": "Бруклин 9-9",
  "4852": "Бруклин 9-9",
  "4853": "Бруклин 9-9",
  "4854": "Бруклин 9-9"
}

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for rec_id, title_ru in mapping.items():
    cursor.execute("UPDATE media SET title_ru = ? WHERE id = ?", (title_ru, rec_id))

conn.commit()
print(f"Updated {len(mapping)} records in the database.")
conn.close()
