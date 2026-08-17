"""
Утилита управления stream_url (онлайн-ссылками) для медиатеки.

Использование:
    # Установить ссылку на сезон (создаёт запись сезона если нет):
    python set_stream_url.py "Сваты 1 сезон" "https://youtube.com/watch?v=..."
    python set_stream_url.py "Во все тяжкие 2 сезон" "https://..."

    # Установить ссылку на весь сериал/фильм:
    python set_stream_url.py "Сваты" "https://youtube.com/watch?v=..."

    # Показать все записи с ссылками:
    python set_stream_url.py
"""
import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

from plugins.media_organizer.core import MEDIA_DB


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _find_records(conn: sqlite3.Connection, title_query: str) -> list:
    """Ищет записи по названию (Python-side, обходит проблему LOWER с кириллицей)."""
    q = title_query.lower()
    rows = conn.execute('SELECT * FROM media').fetchall()
    matches = []
    for r in rows:
        t = (r['title'] or '').lower()
        tr = (r['title_ru'] or '').lower()
        if q in t or q in tr or t in q or tr in q:
            matches.append(dict(r))
    return matches


def _parse_season(label: str) -> tuple[str, int | None]:
    """
    Разбирает 'Сваты 1 сезон' → ('Сваты', 1)
                'Breaking Bad'   → ('Breaking Bad', None)
    """
    m = re.search(r'(\d+)\s*сезон', label, re.IGNORECASE)
    if m:
        season_num = int(m.group(1))
        base = label[:m.start()].strip()
        return base, season_num
    return label.strip(), None


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

def cmd_list():
    """Показывает все записи с их ссылками."""
    with sqlite3.connect(MEDIA_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            'SELECT id, title, title_ru, media_type, parent_id, path, stream_url FROM media ORDER BY id'
        ).fetchall()
        header = f"{'ID':>4}  {'P':>4}  {'Тип':10}  {'Название':35}  {'stream_url'}"
        print(header)
        print('-' * 110)
        for r in rows:
            name = r['title_ru'] or r['title'] or '—'
            su = r['stream_url'] or r['path'] or '—'
            if su.startswith('http') and len(su) > 55:
                su = su[:52] + '...'
            pid = str(r['parent_id'] or '')
            print(f"{r['id']:>4}  {pid:>4}  {r['media_type']:10}  {name:35}  {su}")


def cmd_set(label: str, url: str):
    """Устанавливает stream_url для сериала/фильма или конкретного сезона."""
    base_title, season_num = _parse_season(label)

    with sqlite3.connect(MEDIA_DB) as conn:
        conn.row_factory = sqlite3.Row

        # 1. Ищем родительский сериал/фильм
        parents = _find_records(conn, base_title)
        # Отфильтруем: только записи без parent_id (корневые)
        parents = [r for r in parents if not r.get('parent_id')]
        if not parents:
            print(f"❌ Сериал/фильм «{base_title}» не найден в базе.")
            print("   Сначала добавьте его через медиа-органайзер.")
            return

        parent = parents[0]
        parent_id = parent['id']
        parent_name = parent.get('title_ru') or parent.get('title')

        if season_num is None:
            # Обновляем сам сериал/фильм
            conn.execute('UPDATE media SET stream_url = ? WHERE id = ?', (url, parent_id))
            conn.commit()
            print(f"✅ [{parent_id}] «{parent_name}» → {url}")
            return

        # 2. Ищем запись сезона с parent_id = parent['id']
        season_rows = conn.execute(
            'SELECT * FROM media WHERE parent_id = ?', (parent_id,)
        ).fetchall()

        # Ищем среди дочерних запись с подходящим номером сезона
        season_record = None
        for sr in season_rows:
            t = (sr['title'] or '').lower()
            if f'сезон {season_num}' in t or f'season {season_num}' in t or f's{season_num:02d}' in t:
                season_record = sr
                break
            # Если в title просто "Сваты: Сезон 1" или "Сваты - 1 сезон"
            m = re.search(r'(\d+)', sr['title'] or '')
            if m and int(m.group(1)) == season_num:
                season_record = sr
                break

        if season_record:
            # Обновляем существующую запись сезона
            sid = season_record['id']
            conn.execute('UPDATE media SET stream_url = ? WHERE id = ?', (url, sid))
            conn.commit()
            sname = season_record.get('title_ru') or season_record.get('title')
            print(f"✅ [{sid}] «{sname}» (сезон {season_num} → {parent_name}) → {url}")
        else:
            # Создаём новую запись сезона
            season_title = f"{parent.get('title')} Season {season_num}"
            season_title_ru = f"{parent_name}: Сезон {season_num}"
            conn.execute(
                """INSERT INTO media
                   (disk_name, title, title_ru, media_type, parent_id, stream_url, path, plot)
                   VALUES (?, ?, ?, 'series', ?, ?, '', ?)""",
                (
                    parent.get('disk_name', ''),
                    season_title,
                    season_title_ru,
                    parent_id,
                    url,
                    f"{season_title_ru}. Онлайн: {url}"
                )
            )
            conn.commit()
            print(f"✅ Создана запись «{season_title_ru}» (parent={parent_id}) → {url}")


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) == 3:
        cmd_set(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 1:
        cmd_list()
    else:
        print(__doc__)
