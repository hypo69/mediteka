
"""Запуск плагина media_organizer из командной строки.

Примеры:
    py run_media_organizer.py                          # полное сканирование
    py run_media_organizer.py --title "Фауда"          # JSON для одного тайтла
    py run_media_organizer.py --title "The Bear" --type series
    Больше примеров см в `def main()`
"""
import asyncio
import json
import re
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import header
from src.ai import GoogleGenerativeAI
from plugins.media_organizer.core.media_organizer import (
    INSTRUCTION, MediaAuditor, load_media_paths,
    MediaScanner, _normalize_disk_name, PersistentGenreClassifier,
    MediaOrganizerPlugin
)
from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core import MEDIA_DB
from plugins.media_organizer.core.report_generator import _record_to_md

load_dotenv()

from src.logger import logger


def _launch_web():
    """Запускает веб-сервер и открывает браузер."""
    import subprocess
    import webbrowser
    import time
    import sys
    from src.utils.jjson import j_loads_ns
    from header import __root__

    cfg = j_loads_ns(__root__ / 'src' / 'fastapi' / 'config.json')
    port = cfg.port
    url = f"http://{cfg.host}:{port}"

    try:
        result = subprocess.check_output(["netstat", "-ano"], text=True, stderr=subprocess.DEVNULL)
        for line in result.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                subprocess.call(["taskkill", "/F", "/PID", pid],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"🛑 Убит старый процесс (PID {pid}) на порту {port}")
                time.sleep(1)
    except Exception:
        pass

    print(f"🌐 Запуск веб-интерфейса: {url}")
    subprocess.Popen([sys.executable, "main.py"], cwd=str(__root__))
    time.sleep(2)
    webbrowser.open(url)


async def main():
    parser = argparse.ArgumentParser(
        prog='run_media_organizer.py',
        description='Органайзер медиатеки: сканирование, классификация через Gemini, отчёты, ревизия.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  py run_media_organizer.py
      Без аргументов — запрос имени диска интерактивно.
      Двойной Enter — открывает веб-интерфейс (http://127.0.0.1:3000).

  py run_media_organizer.py --disk "диск 2" --path "E:"
      Полное сканирование диска E:, имя диска "ДИСК 2".

  py run_media_organizer.py --disk "диск 2" --path "E:" --key kazarinov
      То же, но с конкретным Gemini-ключом.

  py run_media_organizer.py --title "Фауда" --disk "диск 2" --type series
      Классифицировать один тайтл и сохранить MD-карточку.

  py run_media_organizer.py --audit --path "E:"
      Ревизия: сверить записи в БД с файлами на диске.

  py run_media_organizer.py --audit --path "E:" "L:" "S:" "Z:"
      Ревизия сразу по нескольким дискам.

  py run_media_organizer.py --disk "диск 2" --path "E:" --format csv
      Сканирование с выводом отчёта в CSV.

  py run_media_organizer.py --rebuild --disk "диск 2"
      Восстановить БД из ДИСК 2.json и переименовать файлы/папки.

  py run_media_organizer.py --force --disk "1" "2" "5" --path "E:" "L:" "S:"
      Удалить JSON и записи БД для каждого диска, затем полностью пересканировать.
      Диски и пути сопоставляются попарно: диск 1 → E:, диск 2 → L:, диск 5 → S:.
"""
    )
    parser.add_argument('--disk', type=str, default=None, metavar='NAME', nargs='+',
                        help='Одно или несколько имён дисков, например "1" "2" "5".')
    parser.add_argument('--path', type=str, default=None, metavar='PATH', nargs='+',
                        help='Один или несколько путей к медиатеке.')
    parser.add_argument('--map', type=str, default=None, metavar='DISK:PATH', nargs='+',
                        help='Явное сопоставление диска и пути.')
    parser.add_argument('--title', type=str, default=None, metavar='TITLE',
                        help='Классифицировать один тайтл.')
    parser.add_argument('--type', type=str, default='series', choices=['series', 'movie'],
                        help='Тип тайтла для --title.')
    parser.add_argument('--format', type=str, default='md', choices=['md', 'csv', 'txt'],
                        help='Формат итогового отчёта.')
    parser.add_argument('--audit', action='store_true', help='Режим ревизии.')
    parser.add_argument('--key', type=str, default=None, metavar='NAME',
                        help='Имя ключа из gemini_keys.json.')
    parser.add_argument('--force', action='store_true',
                        help='Полная перезапись: удалить JSON и записи БД, затем пересканировать.')
    parser.add_argument('--fulldata', type=str, default='y', choices=['y', 'n'],
                        help='Собирать полные данные сериала (сезоны/эпизоды). По умолчанию: y.')
    parser.add_argument('--reset-quota', type=str, nargs='*', metavar='NAME',
                        help='Принудительный сброс дневной квоты.')
    args = parser.parse_args()

    def normalize_path(path_str: str) -> str:
        path_str = path_str.strip()
        if re.match(r'^[A-Z]:[\\/]', path_str, re.IGNORECASE):
            return str(Path(path_str))
        if re.match(r'^[A-Z]:$', path_str, re.IGNORECASE):
            return path_str + '\\'
        if re.match(r'^[A-Z]:[/]+$', path_str, re.IGNORECASE):
            return path_str[0:2] + '\\'
        return path_str

    if args.path:
        # Проверяем на ошибки экранирования кавычек в Windows (когда путь заканчивается на обратный слэш в кавычках: "K:\")
        for p in args.path:
            if '"' in p:
                print(f"❌ Ошибка: В пути обнаружены лишние кавычки: '{p}'")
                print("В Windows обратный слэш перед закрывающей кавычкой (например, \"K:\\\") экранирует её.")
                print("Решение: используйте \"K:\\\\\" (двойной слэш), \"K:/\" (прямой слэш) или пишите путь без кавычек: K:\\")
                return
        args.path = [normalize_path(p) for p in args.path]

    if args.reset_quota is not None:
        from src.secrets.api_key_state import reset_exhausted
        reset_exhausted(args.reset_quota if args.reset_quota else None)
        return

    if args.force:
        if not args.disk or not args.path:
            print("❌ --force требует --disk и --path")
            return
        db = MediaDatabase(MEDIA_DB)
        disk_pairs = list(zip(args.disk, args.path))
        for raw_disk, raw_path in disk_pairs:
            disk_name = raw_disk if raw_disk.upper().startswith("ДИСК") else f"ДИСК {raw_disk}"
            deleted = db.delete_disk(disk_name)
            print(f"🗑  БД: удалено {deleted} записей для {disk_name}")
        print()



    if args.audit:
        from plugins.qbittorrent.qbittorrent import QBittorrentClient
        from src.utils.jjson import j_loads_ns
        from header import __root__
        from src.secrets.api_key_state import load_api_keys

        db = MediaDatabase(MEDIA_DB)
        paths = [Path(p) for p in args.path] if args.path else load_media_paths()
        if not paths:
            print(f"❌ Не заданы пути. Используйте --path или заполните media_paths.txt")
            return
        qbt = None
        try:
            cfg = j_loads_ns(__root__ / 'plugins' / 'qbittorrent' / 'config.json')
            qbt_cfg = cfg
            qbt = QBittorrentClient(qbt_cfg.host, int(qbt_cfg.port), qbt_cfg.username, qbt_cfg.password)
        except Exception as e:
            print(f"⚠️ qBittorrent недоступен: {e}")
            print(f"⚠️ qBittorrent недоступен: {e}")

        gemini = None
        try:
            _, key_names, _ = load_api_keys()
            if key_names:
                gemini = GoogleGenerativeAI(api_key_names=[key_names[0]], system_instruction=INSTRUCTION)
        except Exception as e:
            print(f"⚠️ Gemini недоступен: {e}")

        auditor = MediaAuditor(db, gemini=gemini)
        issues = await auditor.audit()
        if not issues:
            print("✅ Ревизия завершена: несовпадений не найдено.")
        else:
            print(f"⚠️  Найдено несовпадений: {len(issues)}")
            for iss in issues:
                t = iss['type']
                if t == 'missing_season':
                    qbt_status = iss.get('qbt_status')
                    in_qbt = iss.get('in_qbt', False)
                    qbt_info = f" [в qBT: {qbt_status}]" if in_qbt else " [не найден, поиск запущен]"
                    print(f"  📁 {iss['title']} — отсутствует Сезон {iss['season']}{qbt_info}")
                elif t == 'episodes':
                    qbt_status = iss.get('qbt_status')
                    in_qbt = iss.get('in_qbt', False)
                    qbt_info = f" [в qBT: {qbt_status}]" if in_qbt else " [не найден, поиск запущен]"
                    inc = f", неполных: {iss['incomplete']}" if iss.get('incomplete') else ""
                    print(f"  🎬 {iss['title']} С{iss['season']:02d}: есть {iss['actual']}/{iss['expected']} серий{inc} ({iss['size_mb']} MB){qbt_info}")
                elif t == 'incomplete_files':
                    print(f"  ⏳ {iss['title']} С{iss['season']:02d}: {iss['complete']} полных, {iss['incomplete']} неполных ({iss['size_mb']} MB)")
        return

    if not args.disk:
        raw = input("Введите имя диска (например, ДИСК 4): ").strip()
        if not raw:
            raw = input("Имя диска не введено. Нажмите Enter для веб-интерфейса: ").strip()
            if not raw:
                _launch_web()
                return
        args.disk = [raw]

    disk_name = args.disk[0] if args.disk[0].upper().startswith("ДИСК") else f"ДИСК {args.disk[0]}"

    existing_paths = load_media_paths()
    if not args.path and not existing_paths:
        parser.error("--path обязателен, так как пути для сканирования не заданы")
    from src.secrets.api_key_state import load_api_keys

    if args.key:
        _, all_names, _ = load_api_keys()
        if args.key not in all_names:
            print(f"❌ Ключ '{args.key}' не найден. Доступные: {', '.join(all_names)}")
            return
        _api_key_names = [args.key]
    else:
        _, key_names, _ = load_api_keys()
        if not key_names:
            print("❌ Нет доступных активных ключей.")
            return
        _api_key_names = key_names
        print(f"🔑 Используется ключ: {key_names[0]}")

    ai = GoogleGenerativeAI(api_key_names=_api_key_names, system_instruction=INSTRUCTION)
    from src.secrets.api_key_state import update_last_run

    if args.title:
        db = MediaDatabase(MEDIA_DB)
        classifier = PersistentGenreClassifier(tmdb=None, gemini=ai, db=db, disk_name=disk_name)
        is_series = (args.type == 'series')
        info = await classifier._map_category(args.title, [], args.type, args.title, is_series)
        print(json.dumps(info, ensure_ascii=False, indent=2))

        from header import __root__
        out = __root__ / f"{info.get('title', args.title)}.md"
        out.write_text(_record_to_md(info), encoding='utf-8')
        print(f"\nMD: {out}")
    else:
        disk_list = args.disk if args.disk else [disk_name]
        path_list = args.path if args.path else []

        pairs = []
        for i, raw_disk in enumerate(disk_list):
            dn = raw_disk if raw_disk.upper().startswith("ДИСК") else f"ДИСК {raw_disk}"
            dp = [Path(path_list[i])] if i < len(path_list) else ([Path(p) for p in path_list] if path_list else load_media_paths())
            pairs.append((dn, dp))

        for dn, dp in pairs:
            print(f"\n{'='*50}\n► Сканирование: {dn}  →  {[str(x) for x in dp]}\n{'='*50}")
            p = MediaOrganizerPlugin(ai)
            p.report_format = args.format
            p.media_paths = dp
            # Передаем fulldata в метод handle
            result = await p.handle(f'скан медиатеки {dn}', disk_paths=dp, fulldata=(args.fulldata == 'y'))
            print(result)

    update_last_run(_api_key_names[0])


if __name__ == '__main__':
    asyncio.run(main())
