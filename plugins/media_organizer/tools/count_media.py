# -*- coding: utf-8 -*-
from plugins.media_organizer.core import MEDIA_DB
from plugins.media_organizer.core.database import MediaDatabase

db = MediaDatabase(MEDIA_DB)
all_media = db.export_all()

movies = [m for m in all_media if m.get('num_of_seasons', 0) == 0]
series = [m for m in all_media if m.get('num_of_seasons', 0) > 0]

print(f"Всего записей: {len(all_media)}")
print(f"Фильмов: {len(movies)}")
print(f"Сериалов: {len(series)}")
