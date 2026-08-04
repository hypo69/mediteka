import sqlite3
import os
import pandas as pd
import argparse
from pathlib import Path

DB_PATH = r'C:\mediateka\plugins\media_organizer\data\media.db'
SEARCH_ROOT = Path(r'R:\сериалы')

def find_file_by_name(filename):
    print(f"Searching for {filename} in {SEARCH_ROOT}...")
    for root, dirs, files in os.walk(SEARCH_ROOT):
        for file in files:
            if file == filename:
                return Path(root) / file
    return None

def delete_media(file_path_in_db):
    filename = Path(file_path_in_db).name
    
    # Find the actual file on disk
    actual_file = find_file_by_name(filename)
    
    if actual_file:
        try:
            actual_file.unlink()
            print(f"Файл удален: {actual_file}")
            
            # Удаление записи из БД
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM media WHERE path = ?", (file_path_in_db,))
            conn.commit()
            conn.close()
            print(f"Запись удалена из БД: {file_path_in_db}")
            return True
        except Exception as e:
            print(f"Ошибка при удалении файла или записи в БД {file_path_in_db}: {e}")
            return False
    else:
        print(f"File NOT FOUND: {filename}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True, help='Path to CSV with paths to delete')
    parser.add_argument('--execute', action='store_true', help='Execute deletion')
    args = parser.parse_args()
    
    df = pd.read_csv(args.file)
    
    files_to_delete = []
    for _, row in df.iterrows():
        raw_path = row['to_delete'].strip("[]'\"")
        files_to_delete.append(raw_path)
        
    if not args.execute:
        print("Dry run: list of files to delete:")
        for f in files_to_delete:
            print(f)
        print("Run with --execute to proceed.")
        return

    for f in files_to_delete:
        delete_media(f)

if __name__ == '__main__':
    main()
