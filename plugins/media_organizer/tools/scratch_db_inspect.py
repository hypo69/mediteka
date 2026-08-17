import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
from plugins.media_organizer.core import MEDIA_DB
with sqlite3.connect(MEDIA_DB) as conn:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        'SELECT id, title, title_ru, media_type, parent_id, path, stream_url FROM media ORDER BY id'
    ).fetchall()
    for r in rows:
        pid = r['parent_id']
        mtype = r['media_type'] or ''
        title = r['title'] or ''
        path_short = str(r['path'] or '')[:55]
        su = r['stream_url'] or ''
        print(f"id={r['id']:3d} parent={str(pid):5s} type={mtype:10s} title={title!r:35s} stream={su!r:30s} path={path_short!r}")
