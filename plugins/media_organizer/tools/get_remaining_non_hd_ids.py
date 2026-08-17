import sqlite3
db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
# Select IDs for Poirot files that are .m4v but NOT (HD).m4v
cursor.execute("SELECT id FROM media WHERE path LIKE '%Poirot%' AND path LIKE '%.m4v' AND path NOT LIKE '%(HD).m4v%'")
results = cursor.fetchall()
ids_to_delete = [str(r[0]) for r in results]
print(" ".join(ids_to_delete))
conn.close()
