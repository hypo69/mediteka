import sqlite3
import os
import shutil
import pandas as pd
from pathlib import Path

DB_PATH = Path(r'C:\mediateka\plugins\media_organizer\data\media.db')
CANDIDATES_CSV = 'deletion_candidates.csv'
LOG_FILE = 'deletion_dry_run.log'

def dry_run():
    if not os.path.exists(CANDIDATES_CSV):
        print("Файл deletion_candidates.csv не найден. Сначала сгенерируйте кандидатов.")
        return

    df = pd.read_csv(CANDIDATES_CSV)

    print(f"--- РЕЖИМ СИМУЛЯЦИИ (DRY RUN) ---")
    print(f"Всего файлов к удалению: {len(df)}\n")

    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        for _, row in df.iterrows():
            file_path = Path(row['path'])
            msg = f"ОПЕРАЦИЯ: Удаление записи ID {row['id']} и файла '{file_path}'"
            print(msg)
            log.write(msg + '\n')
            
            if file_path.exists():
                log.write(f"  [СТАТУС] Файл существует на диске.\n")
            else:
                log.write(f"  [СТАТУС] ФАЙЛ НЕ НАЙДЕН НА ДИСКЕ.\n")

    print(f"\n--- СИМУЛЯЦИЯ ЗАВЕРШЕНА ---")
    print(f"Подробный лог сохранен в: {LOG_FILE}")
    print(f"Если вы готовы, подтвердите удаление.")

if __name__ == '__main__':
    dry_run()
