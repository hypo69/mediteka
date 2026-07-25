import shutil
from pathlib import Path

# Настройки
SOURCE_ROOT = Path(r"C:\Сериалы")

SERIES_TO_DELETE = [
    "American Odyssey 1 - LostFilm.TV [1080p]",
    "Band of Brothers (Season 1) Пифагор BDRip",
    "Barry",
    "Belgravia.The.Next.Chapter.S01.WEBDL.720p",
    "Berlin.and.the.Lady.with.an.Ermine.S01.WEB-DLRip.LF",
    "Black Bird 1 - LostFilm.TV [MP4]",
    "Brooklin nine nine",
    "Catch-22 1 - LostFilm.TV [1080p]",
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
    "six feet under"
]

def delete_source_folders():
    print(f"=== УДАЛЕНИЕ ИСХОДНЫХ ПАПОК ===")
    for series in SERIES_TO_DELETE:
        folder_path = SOURCE_ROOT / series
        if folder_path.exists():
            print(f"Удаление: {folder_path}")
            if folder_path.is_dir():
                shutil.rmtree(folder_path)
            else:
                folder_path.unlink()
        else:
            print(f"Пропуск (не найдено): {folder_path}")
    print("=== УДАЛЕНИЕ ЗАВЕРШЕНО ===")

if __name__ == "__main__":
    delete_source_folders()
