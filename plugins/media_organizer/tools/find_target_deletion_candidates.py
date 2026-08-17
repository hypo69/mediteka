import sqlite3
import pandas as pd

DB_PATH = r'C:\mediateka\plugins\media_organizer\data\media.db'
TARGET_DIRS = [r'D:\Users\onela\Downloads\01 СЕРИАЛЫ', r'C:\Сериалы']

conn = sqlite3.connect(DB_PATH)

# Using SQL LIKE to match paths starting with target directories
query = "SELECT id, title, path FROM media WHERE " + " OR ".join([f"path LIKE '{d}%'" for d in TARGET_DIRS])

df = pd.read_sql_query(query, conn)
conn.close()

# Save the report
df.to_csv('target_deletion_candidates.csv', index=False, encoding='utf-8')
print(f"Found {len(df)} files in target directories.")
print("Report saved to 'target_deletion_candidates.csv'.")
print(df.to_string())
