import sqlite3
from pathlib import Path
from typing import List, Dict

def analyze_duplicates_dry_run(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query to find duplicates on the same disk
    query = """
        SELECT title, disk_name, id, path, media_size, media_type
        FROM media
        WHERE (title, disk_name) IN (
            SELECT title, disk_name
            FROM media
            GROUP BY title, disk_name
            HAVING COUNT(*) > 1
        )
        ORDER BY title, disk_name, media_size DESC
    """
    
    duplicates = cursor.execute(query).fetchall()
    conn.close()

    if not duplicates:
        print("No duplicates found on the same disk.")
        return

    print(f"{'Title':<40} | {'Disk':<10} | {'Size (MB)':<10} | {'Path/Recommendation'}")
    print("-" * 120)

    current_group = None
    for row in duplicates:
        group_key = (row['title'], row['disk_name'])
        
        if group_key != current_group:
            if current_group is not None:
                print("-" * 120)
            current_group = group_key
            print(f"{row['title'][:40]:<40} | {row['disk_name']:<10} | {row['media_size'] // (1024*1024):<10} | {row['path']}")
            keep_id = row['id']
        else:
            # This is a duplicate to be removed
            print(f"{'':<40} | {'':<10} | {row['media_size'] // (1024*1024):<10} | [DELETE] {row['path']}")

if __name__ == "__main__":
    db_path = Path('plugins/media_organizer/data/media.db')
    analyze_duplicates_dry_run(db_path)
