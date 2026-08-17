import sqlite3
import json
from src.logger import logger

conn = sqlite3.connect(r'C:\mediateka\plugins\media_organizer\data\media.db')
cursor = conn.cursor()

logger.info("=== MEDIA (first 3 rows) ===")
cursor.execute('SELECT * FROM media LIMIT 3')
cols = [desc[0] for desc in cursor.description]
for row in cursor.fetchall():
    logger.info(f'\nID: {row[0]}')
    for i, col in enumerate(cols):
        val = row[i]
        if col in ('genres', 'directors', 'cast', 'rating', 'awards', 'seasons', 'facts', 'similar', 'review'):
            if val:
                try:
                    val = json.loads(val)
                except:
                    pass
        logger.info(f'  {col}: {val}')

# logger.info("\n=== SERIES_EPISODES (first 5 rows) ===")
# cursor.execute('SELECT * FROM series_episodes LIMIT 5')
# cols = [desc[0] for desc in cursor.description]
# for row in cursor.fetchall():
#     logger.info(f'\nID: {row[0]}')
#     for i, col in enumerate(cols):
#         logger.info(f'  {col}: {row[i]}')

logger.info("\n=== DUPLICATES ===")
cursor.execute('SELECT * FROM duplicates LIMIT 5')
logger.info(f'Count: {len(cursor.fetchall())}')

conn.close()
