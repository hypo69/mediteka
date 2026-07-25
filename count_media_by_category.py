# -*- coding: utf-8 -*-
from collections import defaultdict
from plugins.media_organizer.core import MEDIA_DB
from plugins.media_organizer.core.database import MediaDatabase

db = MediaDatabase(MEDIA_DB)
all_media = db.export_all()

# Структура: {category: {'movies': 0, 'series': 0}}
stats = defaultdict(lambda: {'movies': 0, 'series': 0})

for m in all_media:
    category = m.get('main_category') or 'Без категории'
    if m.get('num_of_seasons', 0) > 0:
        stats[category]['series'] += 1
    else:
        stats[category]['movies'] += 1

print(f"{'Категория':<30} | {'Фильмов':<10} | {'Сериалов':<10}")
print("-" * 55)
for category, counts in sorted(stats.items()):
    print(f"{category:<30} | {counts['movies']:<10} | {counts['series']:<10}")
