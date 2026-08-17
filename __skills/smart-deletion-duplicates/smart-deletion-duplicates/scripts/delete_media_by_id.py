import sqlite3
import os
import pandas as pd
import argparse
from pathlib import Path

DB_PATH = r'C:\mediateka\plugins\media_organizer\data\media.db'

def delete_media_by_id(media_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM media WHERE id = ?", (media_id,))
    result = cursor.fetchone()
    
    if not result:
        print(f"Запись с ID {media_id} не найдена в БД.")
        conn.close()
        return False
        
    file_path = result[0]
    conn.close()
    
    # Удаление файла с диска
    path = Path(file_path)
    if path.exists():
        try:
            path.unlink()
            print(f"Файл удален: {file_path}")
        except Exception as e:
            print(f"Ошибка при удалении файла {file_path}: {e}")
            return False
    else:
        print(f"Файл не найден на диске: {file_path}")
    
    # Удаление записи из БД
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM media WHERE id = ?", (media_id,))
        conn.commit()
        conn.close()
        print(f"Запись {media_id} удалена из БД.")
        return True
    except Exception as e:
        print(f"Ошибка при удалении записи {media_id} из БД: {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ids', nargs='+', required=True, help='List of IDs to delete')
    parser.add_argument('--execute', action='store_true', help='Execute deletion')
    args = parser.parse_args()
    
    if not args.execute:
        print(f"Dry run: IDs to delete: {args.ids}")
        print("Run with --execute to proceed.")
        return

    for media_id in args.ids:
        delete_media_by_id(media_id)

if __name__ == '__main__':
    main()
