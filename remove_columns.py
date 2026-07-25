import sqlite3
from pathlib import Path

DB_PATH = Path(r"C:\mediateka\plugins\media_organizer\data\media.db")

def remove_columns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Получаем список всех колонок
    cursor.execute("PRAGMA table_info(media)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Колонки для сохранения
    cols_to_keep = [c for c in columns if c not in ('plot_tts', 'why_watch_tts')]
    
    print(f"Сохраняем колонки: {', '.join(cols_to_keep)}")
    
    # 1. Создаем новую таблицу с правильным SQL
    cols_def = ", ".join([f'"{c}"' for c in cols_to_keep])
    # Получаем определение таблицы через CREATE TABLE
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='media'")
    old_sql = cursor.fetchone()[0]
    
    # Это упрощенный подход, создание новой таблицы через SELECT
    cursor.execute(f"CREATE TABLE media_new AS SELECT {cols_def} FROM media")
    
    # 2. Удаляем старую
    cursor.execute("DROP TABLE media")
    
    # 3. Переименовываем новую
    cursor.execute("ALTER TABLE media_new RENAME TO media")
    
    conn.commit()
    conn.close()
    print("Лишние колонки успешно удалены.")

if __name__ == '__main__':
    remove_columns()
