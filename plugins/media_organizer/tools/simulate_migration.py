import sqlite3
from pathlib import Path
import sys

# Настройки
SOURCE_ROOT = Path(r"C:\Сериалы")
DEST_ROOT = Path(r"Y:\сериалы")
DB_PATH = Path(r"C:\mediateka\plugins\media_organizer\data\media.db")

# Список сериалов для переноса (сокращенный для примера или все)
SERIES_TO_MOVE = [
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

def simulate():
    print(f"=== СИМУЛЯЦИЯ ПЕРЕНОСА ===")
    print(f"Из: {SOURCE_ROOT}")
    print(f"В: {DEST_ROOT}")
    print("-" * 50)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for series_name in SERIES_TO_MOVE:
        old_path = SOURCE_ROOT / series_name
        new_path = DEST_ROOT / series_name
        
        if not old_path.exists():
            print(f"[!] ВНИМАНИЕ: Папка не найдена: {old_path}")
            continue
            
        print(f"\nСериал: {series_name}")
        print(f"  Действие 1: Физическое копирование {old_path} -> {new_path}")
        
        # Поиск в БД
        cursor.execute("SELECT id, path FROM media WHERE path LIKE ?", (f"%{series_name}%",))
        rows = cursor.fetchall()
        
        if rows:
            for row in rows:
                print(f"  Действие 2: БД UPDATE media SET path='{new_path}' WHERE id={row[0]} (старый: {row[1]})")
        else:
            print(f"  [?] БД: Сериал не найден в базе данных.")
            
        # Симуляция проверки торрента
        print(f"  Действие 3: qBittorrent: set_location('{series_name}', '{new_path}')")
        
    conn.close()
    print("\n=== СИМУЛЯЦИЯ ЗАВЕРШЕНА ===")

if __name__ == "__main__":
    simulate()
