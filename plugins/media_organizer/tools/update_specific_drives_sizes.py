import sqlite3
from pathlib import Path
import os

DB_PATH = Path(r'C:\mediateka\plugins\media_organizer\data\media.db')
TARGET_DRIVES = ['O:', 'P:', 'Q:', 'W:']

def update_sizes():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Prepare SQL to select paths for specific drives
    # Note: SQLite LIKE is case-insensitive by default in many configurations, 
    # but using 'O:\\%' is safer for path matching.
    
    query = "SELECT id, path FROM media WHERE " + " OR ".join(["path LIKE ?"] * len(TARGET_DRIVES))
    params = [f"{drive}\\%" for drive in TARGET_DRIVES]
    
    cursor.execute(query, params)
    records = cursor.fetchall()
    
    print(f"Found {len(records)} potential records to check.")
    
    updated_count = 0
    for record_id, file_path_str in records:
        if not file_path_str:
            continue
        
        path = Path(file_path_str)
        
        # Requirement: ТОЛЬКО ФАЙЛЫ
        if path.is_file():
            try:
                size = path.stat().st_size
                cursor.execute("UPDATE media SET media_size = ? WHERE id = ?", (size, record_id))
                updated_count += 1
                if updated_count % 100 == 0:
                    print(f"Updated {updated_count} records...")
            except Exception as e:
                print(f"Error updating {file_path_str}: {e}")
        
    conn.commit()
    conn.close()
    print(f"Done. Updated {updated_count} file size records.")

if __name__ == '__main__':
    update_sizes()
