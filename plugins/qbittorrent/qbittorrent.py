from __future__ import annotations
import json
import re
import unicodedata
import requests
from pathlib import Path
from plugins.plugin import BasePlugin

_CFG_FILE = Path(__file__).parent / "config.json"


def _load_cfg():
    from src.utils.jjson import j_loads_ns
    return j_loads_ns(_CFG_FILE)


class QBittorrentClient:
    """Минимальный клиент qBittorrent Web API."""

    def __init__(self, host: str, port: int, username: str, password: str):
        self.base = f"http://{host}:{port}"
        self.session = requests.Session()
        self._login(username, password)

    def _login(self, username: str, password: str):
        try:
            r = self.session.post(f"{self.base}/api/v2/auth/login",
                                  data={"username": username, "password": password})
            print(f"[qbt] login response: {r.status_code!r} {r.text!r}")
        except Exception:
            # Некоторые версии с bypass localhost не отвечают на /auth/login вовсе
            print("[qbt] login endpoint unavailable, assuming bypass auth")
            return
        if r.text not in ("Ok.", ""):
            raise ConnectionError(f"qBittorrent login failed: {r.text}")

    def torrents(self) -> list[dict]:
        return self.session.get(f"{self.base}/api/v2/torrents/info").json()

    def search_start(self, pattern: str, plugins: str = "all", category: str = "all") -> int | None:
        """Запускает встроенный поиск qBittorrent. Возвращает search_id или None."""
        try:
            r = self.session.post(f"{self.base}/api/v2/search/start",
                                  data={"pattern": pattern, "plugins": plugins, "category": category})
            return r.json().get("id")
        except Exception as e:
            print(f"[qbt] search_start failed: {e}")
            return None

    def search_results(self, search_id: int) -> list[dict]:
        """Возвращает результаты поиска по search_id."""
        try:
            r = self.session.get(f"{self.base}/api/v2/search/results", params={"id": search_id})
            return r.json().get("results", [])
        except Exception:
            return []

    def recheck(self, torrent_hash: str):
        self.session.post(f"{self.base}/api/v2/torrents/recheck",
                          data={"hashes": torrent_hash})

    def files(self, torrent_hash: str) -> list[dict]:
        return self.session.get(f"{self.base}/api/v2/torrents/files",
                                params={"hash": torrent_hash}).json()

    def set_location(self, torrent_hash: str, location: str):
        self.session.post(f"{self.base}/api/v2/torrents/setLocation",
                          data={"hashes": torrent_hash, "location": location})

    def set_category(self, torrent_hash: str, category: str):
        self.session.post(f"{self.base}/api/v2/torrents/setCategory",
                          data={"hashes": torrent_hash, "category": category})

    def add_tags(self, torrent_hash: str, tags: str):
        self.session.post(f"{self.base}/api/v2/torrents/addTags",
                          data={"hashes": torrent_hash, "tags": tags})

    def remove_tags(self, torrent_hash: str, tags: str):
        self.session.post(f"{self.base}/api/v2/torrents/removeTags",
                          data={"hashes": torrent_hash, "tags": tags})

    def create_category(self, category: str):
        self.session.post(f"{self.base}/api/v2/torrents/createCategory",
                          data={"category": category})

    def set_file_priority(self, torrent_hash: str, file_ids: list[int] | str, priority: int):
        if isinstance(file_ids, list):
            file_ids = "|".join(map(str, file_ids))
        self.session.post(f"{self.base}/api/v2/torrents/filePrio",
                          data={"hash": torrent_hash, "id": file_ids, "priority": priority})

    def add_torrent_by_url(self, url: str) -> bool:
        try:
            r = self.session.post(f"{self.base}/api/v2/torrents/add", data={"urls": url})
            return r.status_code == 200
        except Exception as e:
            print(f"[qbt] add_torrent_by_url failed: {e}")
            return False

    def add_torrent_by_file(self, file_content: bytes, filename: str) -> bool:
        try:
            files = {"torrents": (filename, file_content, "application/x-bittorrent")}
            r = self.session.post(f"{self.base}/api/v2/torrents/add", files=files)
            return r.status_code == 200
        except Exception as e:
            print(f"[qbt] add_torrent_by_file failed: {e}")
            return False



# S01E01 / 1x01 / EP01 / Серия 1
_EP_RE = re.compile(
    r'[Ss](\d{1,2})[Ee](\d{1,3})'      # S01E01
    r'|(\d{1,2})[xX](\d{1,3})'          # 1x01
    r'|[Ee][Pp]?(\d{1,3})'              # EP01 / E01
    r'|[Сс]ери[яи]\s*(\d{1,3})',        # Серия 1
)


def _parse_episode(name: str) -> tuple[int, int] | None:
    """Возвращает (season, episode) или None."""
    m = _EP_RE.search(name)
    if not m:
        return None
    if m.group(1):
        return int(m.group(1)), int(m.group(2))
    if m.group(3):
        return int(m.group(3)), int(m.group(4))
    ep = m.group(5) or m.group(6)
    return 1, int(ep)


def check_integrity(client: QBittorrentClient) -> str:
    """Запускает recheck всех торрентов, возвращает сводку."""
    torrents = client.torrents()
    if not torrents:
        return "Торренты не найдены."
    lines = []
    for t in torrents:
        client.recheck(t["hash"])
        state = t.get("state", "unknown")
        progress = t.get("progress", 0) * 100
        lines.append(f"  [{state:>12}] {progress:5.1f}%  {t['name']}")
    return "Recheck запущен для всех торрентов:\n" + "\n".join(lines)


def find_series(client: QBittorrentClient) -> str:
    """Ищет эпизоды сериалов по всем торрентам и показывает пропуски."""
    torrents = client.torrents()
    # series_name -> {(season, ep): filename}
    catalog: dict[str, dict[tuple[int, int], str]] = {}

    for t in torrents:
        try:
            files = client.files(t["hash"])
        except Exception:
            continue
        for f in files:
            name = Path(f["name"]).name
            ep = _parse_episode(name)
            if ep is None:
                continue
            # Имя сериала — название торрента без эпизодной части
            series = _EP_RE.sub("", t["name"]).strip(" .-_")
            catalog.setdefault(series, {})[ep] = name

    if not catalog:
        return "Эпизоды сериалов не обнаружены."

    lines = []
    for series, episodes in sorted(catalog.items()):
        seasons: dict[int, list[int]] = {}
        for s, e in episodes:
            seasons.setdefault(s, []).append(e)

        lines.append(f"\n📺 {series}")
        for s, eps in sorted(seasons.items()):
            eps_sorted = sorted(eps)
            full = set(range(eps_sorted[0], eps_sorted[-1] + 1))
            missing = sorted(full - set(eps_sorted))
            lines.append(f"  Сезон {s}: эпизоды {eps_sorted[0]}–{eps_sorted[-1]}"
                         f"  (есть: {len(eps_sorted)})")
            if missing:
                lines.append(f"    ⚠ Пропущены: {missing}")

    return "Каталог сериалов:" + "".join(lines)


def _build_file_index(search_dirs: list[str]) -> dict[str, Path]:
    """Рекурсивно индексирует все файлы в указанных директориях. filename -> Path"""
    index: dict[str, Path] = {}
    for d in search_dirs:
        for p in Path(d).rglob("*"):
            if p.is_file():
                index[p.name.lower()] = p
    return index


# ============================================
# TRANSLITERATION + FUZZY MATCH
# ============================================

_TRANSLIT = str.maketrans({
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z',
    'и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r',
    'с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh',
    'щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
    'А':'A','Б':'B','В':'V','Г':'G','Д':'D','Е':'E','Ё':'Yo','Ж':'Zh','З':'Z',
    'И':'I','Й':'Y','К':'K','Л':'L','М':'M','Н':'N','О':'O','П':'P','Р':'R',
    'С':'S','Т':'T','У':'U','Ф':'F','Х':'Kh','Ц':'Ts','Ч':'Ch','Ш':'Sh',
    'Щ':'Sch','Ъ':'','Ы':'Y','Ь':'','Э':'E','Ю':'Yu','Я':'Ya',
})


def _normalize(s: str) -> str:
    """Нижний регистр, транслит, только буквы/цифры."""
    s = s.translate(_TRANSLIT)
    s = unicodedata.normalize('NFD', s)
    s = re.sub(r'[^a-z0-9]', ' ', s.lower())
    return re.sub(r'\s+', ' ', s).strip()


def _token_overlap(a: str, b: str) -> float:
    """Доля общих токенов (0..1)."""
    ta, tb = set(_normalize(a).split()), set(_normalize(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def find_torrents_for_title(client: QBittorrentClient, title: str, threshold: float = 0.4) -> list[dict]:
    """Возвращает торренты, название которых fuzzy-совпадает с title."""
    return [
        t for t in client.torrents()
        if _token_overlap(title, t["name"]) >= threshold
    ]


_CATEGORY_CACHE_FILE = Path(__file__).parent / "category_cache.json"


def _load_cache() -> dict[str, str]:
    """Загружает кэш {torrent_hash: category} из файла."""
    try:
        return json.loads(_CATEGORY_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache: dict[str, str]):
    _CATEGORY_CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def assign_categories_from_db(client: QBittorrentClient, db_path: Path, threshold: float = 0.4) -> str:
    """Назначает категории торрентам на основе данных из БД медиатеки.

    Для каждого торрента без категории ищет совпадение по названию в БД.
    Уже обработанные торренты пропускаются (кэш в category_cache.json).

    Args:
        client: Клиент qBittorrent.
        db_path: Путь к SQLite БД медиатеки.
        threshold: Порог fuzzy-совпадения (0..1).

    Returns:
        Строка с итогами.
    """
    import sqlite3
    cache = _load_cache()
    torrents = client.torrents()
    assigned = skipped = no_match = 0
    lines = []

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        db_records = conn.execute(
            "SELECT title, main_category, type FROM media WHERE main_category != '' AND main_category IS NOT NULL"
        ).fetchall()

    for t in torrents:
        h = t["hash"]
        existing_cat = t.get("category", "")

        if h in cache:
            skipped += 1
            continue

        if existing_cat:
            cache[h] = existing_cat
            skipped += 1
            continue

        # Fuzzy-поиск по БД
        best_score, best_record = 0.0, None
        for row in db_records:
            score = _token_overlap(t["name"], row["title"])
            if score > best_score:
                best_score, best_record = score, row

        if best_score < threshold or best_record is None:
            no_match += 1
            lines.append(f"  ❓ {t['name']}  — совпадений не найдено")
            continue

        category = best_record["main_category"]
        client.create_category(category)
        client.set_category(h, category)
        cache[h] = category
        assigned += 1
        lines.append(f"  ✅ {t['name']}  →  {category}  (score={best_score:.2f})")

    _save_cache(cache)
    summary = f"Назначено: {assigned} | Пропущено (уже есть): {skipped} | Без совпадений: {no_match}"
    return summary + ("\n" + "\n".join(lines) if lines else "")


def tag_with_titles(client: QBittorrentClient, ai, batch_size: int = 100) -> str:
    """Проставляет каждому торренту метку с нормализованным названием фильма/сериала через Gemini."""
    import asyncio
    torrents = client.torrents()
    if not torrents:
        return "Торренты не найдены."

    # Пропускаем уже размеченные
    pending = [
        (i, t) for i, t in enumerate(torrents)
        if not any(tag.strip().startswith("title:") for tag in t.get("tags", "").split(","))
    ]
    if not pending:
        return "Все торренты уже размечены."

    tagged = 0
    errors = 0
    lines = []

    for start in range(0, len(pending), batch_size):
        batch = pending[start:start + batch_size]
        numbered = "\n".join(f"{i+1}. {t['name']}" for i, (_, t) in enumerate(batch))
        prompt = (
            "Ниже список торрентов. Для каждого определи название фильма или сериала в формате: "
            '"Русское название (English Title)". '
            "Если фильм русский — только русское название. "
            "Если иностранный — только английское. "
            "Верни ТОЛЬКО JSON-объект, где ключ — номер торрента (1-based), значение — название. "
            'Например: {"1": "Корона (The Crown)", "2": "Breaking Bad"}.\n\n'
            + numbered
        )
        raw = asyncio.run(ai.ask(prompt))
        mapping = _parse_gemini_titles(raw)

        for local_idx, (global_idx, t) in enumerate(batch):
            title = mapping.get(local_idx + 1)
            if not title:
                errors += 1
                lines.append(f"  ❓ [{global_idx+1}] {t['name']}")
                continue
            client.add_tags(t["hash"], f"title:{title}")
            tagged += 1
            lines.append(f"  ✅ [{global_idx+1}] {t['name']}\n      → {title}")

    summary = f"Размечено: {tagged} | Не распознано: {errors}"
    return summary + "\n" + "\n".join(lines)


def _parse_gemini_titles(raw: str | None) -> dict[int, str]:
    """Парсит JSON-ответ Gemini в словарь {1-based номер: название}."""
    if not raw:
        return {}
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if not m:
        return {}
    try:
        data = json.loads(m.group())
        return {int(k): v for k, v in data.items() if str(k).isdigit() and isinstance(v, str)}
    except Exception:
        return {}


def remove_duplicate_tags(client: QBittorrentClient) -> str:
    """Снимает тег 'duplicate' и все теги вида 'dup:...' со всех торрентов."""
    torrents = client.torrents()
    count = 0
    for t in torrents:
        tags = [tag.strip() for tag in t.get("tags", "").split(",") if tag.strip()]
        dup_tags = [tag for tag in tags if tag == "duplicate" or tag.startswith("dup:")]
        if dup_tags:
            client.remove_tags(t["hash"], ",".join(dup_tags))
            count += 1
    return f"Метки сняты с {count} торрентов."


def find_duplicates(client: QBittorrentClient, ai=None, tag_duplicates: bool = False) -> str:
    """Находит дублирующиеся торренты (один и тот же контент из разных источников/качества).

    Сначала группирует по fuzzy-совпадению токенов, затем уточняет через Gemini.
    """
    torrents = client.torrents()
    if not torrents:
        return "Торренты не найдены."

    names = [t["name"] for t in torrents]
    n = len(names)

    # Матрица схожести: пары с overlap >= 0.35
    candidates: list[tuple[int, int]] = []
    for i in range(n):
        for j in range(i + 1, n):
            if _token_overlap(names[i], names[j]) >= 0.35:
                candidates.append((i, j))

    if not candidates and ai is None:
        return "Дубликаты не обнаружены (fuzzy-анализ)."

    # Если есть AI — отправляем кандидатов батчами по 100
    if ai is not None:
        import asyncio

        # Собираем уникальные индексы из fuzzy-кандидатов
        candidate_indices = sorted({idx for pair in candidates for idx in pair})
        if not candidate_indices:
            return "Дубликаты не обнаружены."

        BATCH = 100
        all_groups: list[list[int]] = []
        seen: set[int] = set()

        for start in range(0, len(candidate_indices), BATCH):
            batch_indices = candidate_indices[start:start + BATCH]
            numbered = "\n".join(f"{idx+1}. {names[idx]}" for idx in batch_indices)
            prompt = (
                "Ниже список торрентов (номер соответствует позиции в общем списке). "
                "Найди группы дубликатов — торренты, которые представляют один и тот же фильм или сериал, "
                "но отличаются источником, качеством, языком или оформлением названия. "
                "Верни ТОЛЬКО JSON-массив групп с теми же номерами, например: "
                "[[5,12],[3,7]]. Если дубликатов нет — верни [].\n\n"
                + numbered
            )
            raw = asyncio.run(ai.ask(prompt))
            for group in _parse_gemini_groups(raw, names):
                # Фильтруем уже включённые индексы и группы из одного элемента
                clean = [i for i in group if i not in seen]
                if len(clean) > 1:
                    all_groups.append(clean)
                    seen.update(clean)

        groups = all_groups
    else:
        # Строим группы из fuzzy-кандидатов (union-find)
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for i, j in candidates:
            pi, pj = find(i), find(j)
            if pi != pj:
                parent[pi] = pj

        from collections import defaultdict
        buckets: dict[int, list[int]] = defaultdict(list)
        for idx in range(n):
            buckets[find(idx)].append(idx)
        groups = [idxs for idxs in buckets.values() if len(idxs) > 1]

    if not groups:
        return "Дубликаты не обнаружены."

    tagged = 0
    lines = [f"Найдено групп дубликатов: {len(groups)}\n"]
    for g_idx, group in enumerate(groups, 1):
        lines.append(f"Группа {g_idx}:")
        for idx in group:
            t = torrents[idx]
            size_gb = t.get("size", 0) / 1024**3
            lines.append(f"  [{idx+1:>3}] {t['name']}  ({size_gb:.1f} GB)  [{t.get('state','?')}]")
            if tag_duplicates:
                # Тег 'duplicate' + отдельный тег для каждого дубля в группе
                others = [torrents[i]["name"][:50] for i in group if i != idx]
                dup_tags = "duplicate," + ",".join(f"dup:{name}" for name in others)
                client.add_tags(t["hash"], dup_tags)
                tagged += 1
    if tag_duplicates:
        lines.append(f"\n🏷 Тег 'duplicate' проставлен: {tagged} торрентов")
    return "\n".join(lines)


def _parse_gemini_groups(raw: str | None, names: list[str]) -> list[list[int]]:
    """Парсит JSON-ответ Gemini в список групп индексов (0-based)."""
    if not raw:
        return []
    import json, re
    m = re.search(r'\[.*\]', raw, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group())
        if not data or not isinstance(data[0], list):
            return []
        # Gemini возвращает 1-based номера
        return [[i - 1 for i in group if 1 <= i <= len(names)] for group in data if len(group) > 1]
    except Exception:
        return []


def _build_dir_index(search_dirs: list[str], min_size_mb: int = 100) -> dict[str, Path]:
    """Индексирует папки в указанных директориях (только те, что содержат медиафайлы).
    Возвращает {dir_name_lower: Path}
    """
    _MEDIA_EXT = {".mkv", ".mp4", ".avi", ".m4v", ".mov", ".ts", ".wmv"}
    index: dict[str, Path] = {}

    def _has_media(d: Path) -> bool:
        return any(f.suffix.lower() in _MEDIA_EXT for f in d.rglob("*") if f.is_file())

    for root in search_dirs:
        root_path = Path(root)
        if not root_path.exists():
            continue
        # Добавляем саму корневую и все подпапки
        for d in [root_path] + [p for p in root_path.rglob("*") if p.is_dir()]:
            if _has_media(d):
                index[d.name.lower()] = d
    return index


def relocate_missing_ai(client: QBittorrentClient, search_dirs: list[str], ai) -> str:
    """Находит торренты с утерянными файлами и исправляет путь через Gemini.

    Алгоритм:
    1. Собирает все папки с медиафайлами из search_dirs
    2. Для каждого торрента с missingFiles спрашивает Gemini какую папку выбрать
    3. Устанавливает новое расположение и запускает recheck
    """
    import asyncio

    torrents = [t for t in client.torrents() if t.get("state") in ("missingFiles", "error")]
    if not torrents:
        return "Торрентов с утерянными файлами не найдено."

    print(f"Индексирую папки в {search_dirs} ...")
    dir_index = _build_dir_index(search_dirs)
    dir_names = sorted(dir_index.keys())
    print(f"Найдено папок: {len(dir_names)}")

    results = []
    BATCH = 80  # папок в одном запросе

    for t in torrents:
        torrent_name = t["name"]
        current_path = t.get("save_path", "")

        # Сначала пробуем fuzzy быстрый проход
        best_fuzzy = max(dir_names, key=lambda d: _token_overlap(torrent_name, d), default=None)
        fuzzy_score = _token_overlap(torrent_name, best_fuzzy) if best_fuzzy else 0.0

        if fuzzy_score >= 0.6:
            # Достаточно уверенное совпадение — AI не нужен
            found_dir = dir_index[best_fuzzy]
        else:
            # Спрашиваем Gemini: отправляем название торрента + батч папок
            found_dir = None
            for b_start in range(0, len(dir_names), BATCH):
                batch_dirs = dir_names[b_start:b_start + BATCH]
                dirs_list = "\n".join(f"{i+1}. {d}" for i, d in enumerate(batch_dirs))
                prompt = (
                    f"Торрент: \"{torrent_name}\"\n"
                    f"Текущий путь: \"{current_path}\"\n\n"
                    "Ниже список папок на диске. "
                    "Определи номер папки, которая скорее всего содержит файлы этого торрента. "
                    "Названия могут сильно отличаться от названия торрента — "
                    "учитывай транслитерацию, перевод, сезон, год. "
                    "Верни ТОЛЬКО номер папки (1-based) или 0 если ничего не подходит.\n\n"
                    + dirs_list
                )
                raw = asyncio.run(ai.ask(prompt))
                num = _parse_int(raw)
                if num and 1 <= num <= len(batch_dirs):
                    found_dir = dir_index[batch_dirs[num - 1]]
                    break

        if found_dir:
            # Для сериалов: если нашли подпапку сезона — устанавливаем родительскую
            save_path = str(found_dir.parent if _looks_like_season_dir(found_dir) else found_dir)
            client.set_location(t["hash"], save_path)
            client.recheck(t["hash"])
            results.append(f"  ✅ {torrent_name}\n     → {save_path}")
        else:
            results.append(f"  ❌ {torrent_name}: папка не найдена")

    return f"Обработано {len(torrents)} торрентов:\n" + "\n".join(results)


def _looks_like_season_dir(d: Path) -> bool:
    """Труе, если папка похожа на папку сезона (Season 1, S01, Сезон 2 и т.п.)."""
    return bool(re.search(r'(?i)(season|s\d{2}|сезон)\s*\d', d.name))


def _parse_int(raw: str | None) -> int | None:
    """Извлекает первое целое число из строки ответа Gemini."""
    if not raw:
        return None
    m = re.search(r'\b(\d+)\b', raw.strip())
    return int(m.group(1)) if m else None


def relocate_missing(client: QBittorrentClient, search_dirs: list[str]) -> str:
    """Находит торренты с утерянными файлами и обновляет их расположение."""
    torrents = [t for t in client.torrents() if t.get("state") == "missingFiles"]
    if not torrents:
        return "Торрентов с утерянными файлами не найдено."

    print(f"Индексирую файлы в {search_dirs} ...")
    index = _build_file_index(search_dirs)

    results = []
    for t in torrents:
        try:
            t_files = client.files(t["hash"])
        except Exception:
            results.append(f"  ⚠ {t['name']}: не удалось получить список файлов")
            continue

        # Берём первый файл торрента как ориентир для новой папки
        found_dir: Path | None = None
        for f in t_files:
            fname = Path(f["name"]).name.lower()
            if fname in index:
                found_dir = index[fname].parent
                break

        if found_dir:
            client.set_location(t["hash"], str(found_dir))
            client.recheck(t["hash"])
            results.append(f"  ✅ {t['name']}\n     → {found_dir}")
        else:
            results.append(f"  ❌ {t['name']}: файлы не найдены в указанных директориях")

    return f"Обработано {len(torrents)} торрентов:\n" + "\n".join(results)


class QBittorrentPlugin(BasePlugin):
    name = "qbittorrent"

    def __init__(self, ai_model):
        super().__init__(ai_model)
        self.client: QBittorrentClient | None = None
        self.search_dirs: list[str] = []

    def _get_client(self) -> QBittorrentClient:
        if self.client is None:
            cfg = _load_cfg()
            self.client = QBittorrentClient(
                host=cfg.host,
                port=int(cfg.port),
                username=cfg.username,
                password=cfg.password,
            )
        return self.client

    async def _handle(self, message: str) -> str | None:
        msg = message.lower()

        if "торрент" not in msg and "qbit" not in msg and "сериал" not in msg:
            return None

        client = self._get_client()

        if any(w in msg for w in ("проверить", "целостность", "recheck", "проверка")):
            return check_integrity(client)

        if any(w in msg for w in ("сериал", "эпизод", "серии", "найти")):
            return find_series(client)

        # «найти файлы C:\Movies D:\Films» — задать директории и запустить поиск
        if any(w in msg for w in ("утерян", "relocate", "найди файлы", "найти файлы")):
            # Извлекаем пути из сообщения (всё после ключевого слова)
            parts = message.split()
            dirs = [p for p in parts if Path(p).exists() and Path(p).is_dir()]
            if dirs:
                self.search_dirs = dirs
            if not self.search_dirs:
                return ("Укажи директории для поиска, например:\n"
                        "найди файлы C:\\Movies D:\\Films")
            return relocate_missing(client, self.search_dirs)

        # Общий список торрентов
        torrents = client.torrents()
        if not torrents:
            return "Торренты не найдены."
        lines = [f"  {t['name']}  [{t.get('state','?')}]  "
                 f"{t.get('progress',0)*100:.1f}%" for t in torrents]
        return "Торренты:\n" + "\n".join(lines)
