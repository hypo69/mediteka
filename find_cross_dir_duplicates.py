import sqlite3
import pandas as pd

DB_PATH = r'C:\mediateka\plugins\media_organizer\data\media.db'
TARGET_DIRS = (r'D:\Users\onela\Downloads\01 СЕРИАЛЫ', r'C:\Сериалы')

conn = sqlite3.connect(DB_PATH)

# Get all records
df = pd.read_sql_query("SELECT id, title, path FROM media WHERE path IS NOT NULL AND path != ''", conn)
conn.close()

# Identify target records (in download/temp folders)
df['is_target'] = df['path'].str.startswith(TARGET_DIRS)

# Find titles that appear in BOTH target and non-target locations
titles_in_target = set(df[df['is_target']]['title'])
titles_in_other = set(df[~df['is_target']]['title'])

common_titles = titles_in_target.intersection(titles_in_other)

# Get candidates for deletion
candidates = df[df['is_target'] & df['title'].isin(common_titles)]

# Save report
candidates.to_csv('target_duplicates_report.csv', index=False)
print(f"Found {len(candidates)} candidates for deletion in target directories.")
print(candidates.to_string())
