import sqlite3
import shutil
import sys
from pathlib import Path

# Добавляем корень проекта в путь импорта для доступа к плагинам
sys.path.insert(0, str(Path(__file__).parent))

from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg

# Настройки
SOURCE_ROOT = Path(r"C:\Сериалы")
DEST_ROOT = Path(r"Y:\сериалы")
DB_PATH = Path(r"C:\mediateka\plugins\media_organizer\data\media.db")

SERIES_TO_PROCESS = [
    "Citadel. Honey Bunny 1 - LostFilm.TV [1080p]",
    "City of God. The Fight Rages On 1 - LostFilm.TV [1080p]",
    "Fleabag",
    "Fosse.Verdon.S01.1080p.TVShows",
    "Fringe",
    "Fubar",
    "Halef.s01.WEB-DLRip1080p",
    "His and Hers 1 - LostFilm.TV [1080p]",
    "Homeland",
    "I.Will.Find.You.S01.1080p.NF.WEB-DL.H.264-EniaHD",
    "Justified.S06.Jaskier.WEB-DLRip",
    "Kan Cicekleri.s01.WEB-DLRip720p",
    "Knives.Out.2019.DVO.HDRip",
    "Konec.sveta.S01.WEB-DLRip.25Kuzmich",
    "Last Resort 1 - LostFilm.TV [720p]",
    "Last Samurai Standing 1 - LostFilm.TV [1080p]",
    "Legends",
    "Les Miserables 1 - LostFilm.TV [1080p]",
    "LEVIATHAN.1989.US.BD",
    "Line.of.Duty.XviD.TVShows",
    "Mechta Esrefa",
    "Na voyne kak na voyne",
    "Nevskiy.WEB-DL.(1080p).lunkin",
    "Queen of the South 5 - LostFilm.TV [1080p]",
    "Scrubs Season 2 1080 AI",
    "Scrubs Season 3 1080 AI",
    "Scrubs Season 4 1080 AI",
    "Severance 2 - LostFilm.TV [1080p]",
    "six feet under",
    "American Odyssey 1 - LostFilm.TV [1080p]",
    "Band of Brothers (Season 1) Пифагор BDRip",
    "Barry",
    "Belgravia.The.Next.Chapter.S01.WEBDL.720p",
    "Berlin.and.the.Lady.with.an.Ermine.S01.WEB-DLRip.LF",
    "Black Bird 1 - LostFilm.TV [MP4]",
    "Brooklin nine nine",
    "Catch-22 1 - LostFilm.TV [1080p]"
]

def smart_copy(src, dst):
    if src.is_file():
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            print(f"   Файл '{dst.name}' уже скопирован и совпадает по размеру. Пропускаем.")
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    elif src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.rglob('*'):
            if item.is_file():
                rel_path = item.relative_to(src)
                target = dst / rel_path
                if target.exists() and target.stat().st_size == item.stat().st_size:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)

def migrate_series(series_name, qbt_client):
    print(f"\n--- Начало переноса: {series_name} ---")
    
    old_path = SOURCE_ROOT / series_name
    new_path = DEST_ROOT / series_name
    
    # Проверка существования источника
    if not old_path.exists():
        if new_path.exists():
            print(f"   [i] Папка источника не найдена, но папка назначения уже существует: {new_path}")
        else:
            raise Exception(f"Источник не найден: {old_path}")
            
    # 1. Копирование файлов
    print(f"1. Копирую файлы из {old_path} в {new_path}...")
    if old_path.exists():
        smart_copy(old_path, new_path)
        print("   Копирование успешно.")
    else:
        print("   Пропускаем копирование (источник отсутствует, папка назначения уже существует).")
    
    # 2. Обновление БД
    print(f"2. Обновляю БД...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, path FROM media")
    all_rows = cursor.fetchall()
    
    rows_to_update = []
    old_path_str = str(old_path).lower()
    for row_id, current_path in all_rows:
        if not current_path:
            continue
        cur_path_lower = current_path.lower()
        if cur_path_lower == old_path_str:
            rows_to_update.append((row_id, current_path, True))
        elif cur_path_lower.startswith(old_path_str + "\\"):
            rows_to_update.append((row_id, current_path, False))
            
    if not rows_to_update:
        new_path_str = str(new_path).lower()
        already_updated = False
        for row_id, current_path in all_rows:
            if current_path and current_path.lower() == new_path_str:
                already_updated = True
                break
        if already_updated:
            print("   [i] Путь в БД уже был обновлен ранее.")
        else:
            print(f"   [!] Предупреждение: В БД не найдено записей с путем {old_path}")
    else:
        for row_id, current_path, is_exact in rows_to_update:
            if is_exact:
                updated_path = str(new_path)
            else:
                relative_part = current_path[len(old_path_str):]
                updated_path = str(new_path) + relative_part
            print(f"   Обновляю путь в БД: id={row_id}, '{current_path}' -> '{updated_path}'")
            cursor.execute("UPDATE media SET path = ? WHERE id = ?", (updated_path, row_id))
    conn.commit()
    conn.close()
    print("   БД обновлена.")
    
    # 3. Обновление торрентов
    print(f"3. Обновляю путь в qBittorrent...")
    torrents = qbt_client.torrents()
    
    # Ищем торрент, имя которого совпадает с именем папки
    found = False
    for t in torrents:
        if t['name'] == series_name:
            print(f"   Нашел торрент: {t['name']} (Hash: {t['hash']})")
            qbt_client.set_location(t['hash'], str(new_path))
            print(f"   Путь торрента обновлен на {new_path}")
            found = True
            break
    
    if not found:
        print("   [!] Торрент не найден в qBittorrent (это нормально, если сериал был добавлен вручную).")
    
    print(f"--- Успешно перенесен: {series_name} ---")

if __name__ == "__main__":
    import traceback
    # Инициализация qBittorrent
    try:
        cfg = _load_cfg()
        qbt_client = QBittorrentClient(
            host=cfg.host,
            port=int(cfg.port),
            username=cfg.username,
            password=cfg.password,
        )
        print("✅ Клиент qBittorrent подключен")
    except Exception as e:
        print(f"❌ Ошибка подключения к qBittorrent: {e}")
        sys.exit(1)

    for series in SERIES_TO_PROCESS:
        while True:
            try:
                migrate_series(series, qbt_client)
                break
            except Exception as e:
                print(f"\n!!! ОШИБКА при переносе {series}:")
                traceback.print_exc()
                while True:
                    response = input(f"\n[?] Ошибка при переносе '{series}'.\nПродолжить со следующего (c/продолжить),\nПовторить текущий (r/повторить),\nОстановиться (s/остановиться)? [c/r/s]: ").strip().lower()
                    if response in ('c', 'continue', 'продолжить', 'п'):
                        break_outer = True
                        break
                    elif response in ('r', 'retry', 'повторить', 'попробовать', 'р'):
                        break_outer = False
                        break
                    elif response in ('s', 'stop', 'остановиться', 'о'):
                        print("Выход по требованию пользователя.")
                        sys.exit(1)
                if break_outer:
                    break

