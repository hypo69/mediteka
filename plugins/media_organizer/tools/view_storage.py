import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'plugins' / 'media_organizer' / 'data' / 'media.db'

def view_storage_table():
    if not DB_PATH.exists():
        print("База данных не найдена.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM storage")
        rows = cursor.fetchall()
        print("Данные в таблице storage:")
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Ошибка при чтении: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    view_storage_table()
