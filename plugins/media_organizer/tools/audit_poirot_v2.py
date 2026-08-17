import sqlite3
import os
from pathlib import Path

DB_PATH = r'C:\mediateka\plugins\media_organizer\data\media.db'
POIROT_DIR = Path(r"R:\сериалы\Agatha Christie's Poirot")

def audit_poirot():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, path FROM media WHERE path LIKE ?", (f'%{str(POIROT_DIR)}%',))
    db_records = cursor.fetchall() # list of (id, path)
    conn.close()

    db_paths = {Path(p): i for i, p in db_records}
    
    disk_files = []
    for root, _, files in os.walk(POIROT_DIR):
        for file in files:
            if file.endswith(('.m4v', '.mkv', '.avi')):
                disk_files.append(Path(root) / file)
                
    print(f"--- АУДИТ ПУАРО ---")
    
    # 1. Файлы на диске, отсутствующие в БД (или не-HD дубликаты)
    print(f"\nФайлы на диске (всего {len(disk_files)}):")
    non_hd_on_disk = []
    for f in disk_files:
        is_hd = '(HD)' in f.name
        print(f"  [{'HD' if is_hd else 'NON-HD'}] {f.name}")
        if not is_hd:
            non_hd_on_disk.append(f)
            
    # 2. Записи в БД, отсутствующие на диске
    print(f"\nЗаписи в БД (всего {len(db_paths)}):")
    orphaned_db_records = []
    for p, i in db_paths.items():
        if not p.exists():
            print(f"  [MISSING ON DISK] {p.name} (ID: {i})")
            orphaned_db_records.append(i)
        else:
            print(f"  [OK] {p.name} (ID: {i})")

    return non_hd_on_disk, orphaned_db_records

if __name__ == '__main__':
    audit_poirot()
