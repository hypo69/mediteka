import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
from plugins.media_organizer.core import MEDIA_DB
print('DB path:', MEDIA_DB)

with sqlite3.connect(MEDIA_DB) as conn:
    cols = [c[1] for c in conn.execute('PRAGMA table_info(media)').fetchall()]
    if 'stream_url' not in cols:
        conn.execute('ALTER TABLE media ADD COLUMN stream_url TEXT')
        conn.commit()
        print('Колонка stream_url добавлена')
    else:
        print('Колонка stream_url уже есть')

    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT title, title_ru, path, stream_url FROM media WHERE LOWER(title) LIKE '%svaty%' OR LOWER(title) LIKE '%swat%' OR LOWER(title_ru) LIKE '%swat%' LIMIT 5"
    ).fetchall()
    print(f'Найдено записей: {len(rows)}')
    for r in rows:
        print(f'  title={r["title"]!r}, path={r["path"]!r:.60s}, stream_url={r["stream_url"]!r}')
