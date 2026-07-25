import sqlite3

conn = sqlite3.connect(r'C:\mediateka\plugins\media_organizer\media.db')
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', [row[0] for row in cursor.fetchall()])

# Media columns
cursor.execute('PRAGMA table_info(media)')
print('\nmedia columns:')
for row in cursor.fetchall():
    print(f'  {row}')

# series_episodes columns
cursor.execute('PRAGMA table_info(series_episodes)')
print('\nseries_episodes columns:')
for row in cursor.fetchall():
    print(f'  {row}')

conn.close()
