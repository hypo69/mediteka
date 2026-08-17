"""Скрипт для заполнения пустых метаданных в БД путём запросов к Gemini.

Запускает поэтапное обогащение записей с незаполненными обязательными полями:
- plot, atmosphere, why_watch, mood, final_verdict, quote

Скрипт работает напрямую с GenreClassifier (не через MediaOrganizerPlugin),
чтобы заполнять поля у movie-, series-, season- и episode-записей независимо.

Использование:
    python fill_missing_metadata.py
    python fill_missing_metadata.py --disk "ДИСК 1"
    python fill_missing_metadata.py --type movie
    python fill_missing_metadata.py --type series
    python fill_missing_metadata.py --type season
    python fill_missing_metadata.py --limit 50
"""
import asyncio
import sqlite3
import argparse
from pathlib import Path
from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core.genre_classifier import GenreClassifier
from src.ai import GoogleGenerativeAI


# Настройки
DB_PATH = Path('plugins/media_organizer/data/media.db')

# Поля, которые считаются обязательными для «полной» записи
REQUIRED_FIELDS = ('plot', 'atmosphere', 'why_watch', 'mood', 'final_verdict', 'quote')


def get_incomplete_records(conn, media_type: str = None, disk_name: str = None, limit: int = 0) -> list:
    """Выбрать записи с хотя бы одним пустым обязательным полем."""
    conditions = ["(" + " OR ".join([f"({f} IS NULL OR {f} = '')" for f in REQUIRED_FIELDS]) + ")"]
    params = []
    if media_type:
        conditions.append("media_type = ?")
        params.append(media_type)
    if disk_name:
        conditions.append("disk_name = ?")
        params.append(disk_name)
    where_clause = " AND ".join(conditions)
    sql = f"SELECT id, title, disk_name, media_type, year FROM media WHERE {where_clause} ORDER BY media_type, title"
    if limit:
        sql += f" LIMIT {limit}"
    conn.row_factory = sqlite3.Row
    return conn.execute(sql, params).fetchall()


async def fill_missing_metadata(media_type: str = None, disk_name: str = None, limit: int = 0):
    db = MediaDatabase(DB_PATH)

    with sqlite3.connect(DB_PATH) as conn:
        records = get_incomplete_records(conn, media_type=media_type, disk_name=disk_name, limit=limit)

    if not records:
        print("✅ Все записи уже заполнены, нечего обновлять.")
        return

    print(f"📋 Найдено {len(records)} записей с незаполненными полями.")

    # Инициализация классификатора
    ai_model = GoogleGenerativeAI(api_key_names=['davidka'])
    classifier = GenreClassifier(tmdb=None, gemini=ai_model)

    for rec in records:
        title = rec['title']
        rec_disk_name = rec['disk_name']
        rec_type = rec['media_type'] or 'movie'
        rec_id = rec['id']

        print(f"\n🔄 [{rec_type}] {title} ({rec_disk_name})")

        try:
            # Получаем актуальную запись из БД
            existing = db.get_media(rec_disk_name, title)
            if not existing:
                # Ищем по id напрямую
                with sqlite3.connect(DB_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    row = conn.execute("SELECT * FROM media WHERE id = ?", (rec_id,)).fetchone()
                    existing = dict(row) if row else {}

            if not existing:
                print(f"   ⚠️  Запись {title} не найдена в БД, пропускаем")
                continue

            # Классифицируем только если запись сильно не заполнена
            # (запрашиваем только поля plot/verdict/quote)
            is_series = rec_type in ('series',)
            classified = await classifier.classify(
                raw_name=title,
                path=existing.get('path', ''),
                is_series=is_series
            )
            if not classified:
                print(f"   ❌ Классификатор вернул пустой результат для {title}")
                continue

            # Обновляем только пустые поля (не перезаписываем существующие)
            update_fields = {}
            for field in REQUIRED_FIELDS:
                existing_val = existing.get(field)
                new_val = classified.get(field)
                if (not existing_val) and new_val:
                    update_fields[field] = new_val

            # Также обновляем список facts/similar/review если они пусты
            for field in ('facts', 'similar', 'review'):
                existing_val = existing.get(field)
                new_val = classified.get(field)
                if not existing_val and new_val:
                    update_fields[field] = new_val

            if not update_fields:
                print(f"   ℹ️  Нет новых данных для обновления {title}")
                continue

            # Сохраняем обогащённую запись
            merged = {**existing, **update_fields}
            db.save_media(rec_disk_name, rec_type, merged)
            print(f"   ✅ Обновлено: {', '.join(update_fields.keys())}")

        except Exception as e:
            print(f"   ❌ Ошибка при обновлении {title}: {e}")

    print("\n✅ Процесс заполнения метаданных завершён.")


def main():
    parser = argparse.ArgumentParser(description="Заполнение пустых метаданных медиабиблиотеки через Gemini.")
    parser.add_argument('--disk', type=str, default=None, help='Фильтр по имени диска')
    parser.add_argument('--type', type=str, choices=['movie', 'series', 'season', 'episode'],
                        default=None, dest='media_type', help='Фильтр по типу записи')
    parser.add_argument('--limit', type=int, default=0, help='Максимальное количество записей для обновления')
    args = parser.parse_args()

    asyncio.run(fill_missing_metadata(
        media_type=args.media_type,
        disk_name=args.disk,
        limit=args.limit
    ))


if __name__ == '__main__':
    main()
