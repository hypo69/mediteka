import sqlite3
from pathlib import Path

DB_PATH = Path(r"C:\mediateka\plugins\media_organizer\data\media.db")

def update_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверка наличия колонок перед добавлением
    cursor.execute("PRAGMA table_info(media)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'actual_size' not in columns:
        cursor.execute("ALTER TABLE media ADD COLUMN actual_size INTEGER")
        print("Добавлена колонка actual_size")
        
    if 'size_delta' not in columns:
        cursor.execute("ALTER TABLE media ADD COLUMN size_delta INTEGER")
        print("Добавлена колонка size_delta")
        
    conn.commit()
    conn.close()
    print("Схема БД обновлена.")

if __name__ == '__main__':
    update_schema()
