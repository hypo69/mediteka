import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(r"C:\mediateka\plugins\media_organizer\data\media.db")

def generate_report():
    conn = sqlite3.connect(DB_PATH)
    # Используем pandas для удобного формирования отчета
    df = pd.read_sql_query("SELECT title, path, actual_size, size_delta FROM media WHERE size_delta != 0", conn)
    conn.close()
    
    if df.empty:
        print("Расхождений в размерах не обнаружено.")
    else:
        print(f"Найдено расхождений: {len(df)}")
        report_path = Path("audit_discrepancy_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Отчет о расхождениях размеров файлов\n\n")
            f.write(df.to_markdown(index=False))
        print(f"Отчет сохранен в {report_path}")

if __name__ == '__main__':
    generate_report()
