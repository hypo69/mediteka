import sqlite3

db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all remaining empty title_ru
cursor.execute('SELECT id, path, title FROM media WHERE title_ru IS NULL OR title_ru = ""')
remaining_records = cursor.fetchall()

# Rules based on pattern analysis
def infer_title(path, title):
    if not path: return None
    path_lower = path.lower()
    
    # Inference rules
    if 'бруклин 9-9' in path_lower or 'brooklyn nine-nine' in path_lower:
        return 'Бруклин 9-9'
    if 'прослушка' in path_lower or 'the wire' in path_lower:
        return 'Прослушка'
    if 'американцы' in path_lower or 'the.americans' in path_lower:
        return 'Американцы'
    if 'щит' in path_lower or 'the shield' in path_lower:
        return 'Щит'
    if '500 дней лета' in path_lower:
        return '500 дней лета'
    
    # Generic cleanup for some other known cases or just return title
    # For now, let's keep it simple to avoid false positives
    return None

updated_count = 0
for rec_id, path, title in remaining_records:
    inferred = infer_title(path, title)
    if inferred:
        cursor.execute("UPDATE media SET title_ru = ? WHERE id = ?", (inferred, rec_id))
        updated_count += 1

conn.commit()
print(f"Updated {updated_count} records in the database.")
conn.close()
