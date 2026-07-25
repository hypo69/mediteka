import sqlite3
import pandas as pd

DB_PATH = r'C:\mediateka\plugins\media_organizer\data\media.db'

conn = sqlite3.connect(DB_PATH)
query = """
SELECT id, title, disk_name, path
FROM media
WHERE title IN (
    SELECT title FROM media GROUP BY title HAVING COUNT(*) > 1
)
ORDER BY title, disk_name
"""
df = pd.read_sql_query(query, conn)
conn.close()

# Save to CSV for easy review
df.to_csv('all_duplicates_with_ids.csv', index=False, encoding='utf-8')
print("Report saved to 'all_duplicates_with_ids.csv'.")
print(df.to_string())
