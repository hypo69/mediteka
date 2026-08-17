# Модуль `plugins/media_organizer/tools` — Инструменты управления медиатекой

## Назначение
Набор консольных утилит и скриптов для работы с базой данных и дисками медиатеки:
- `run_media_organizer.py`: основной CLI-раннер сканирования дисков, разметки тайтлов и генерации отчетов.
- `run_dry_run.py`: тестовый запуск сканирования без внесения изменений в БД.
- `fill_missing_metadata.py`: интеллектуальное заполнение пропущенных метаданных через AI.
- `enrich_incomplete_records.py`: обогащение неполных записей карточек тайтлов.
- `audit_disk.py`, `audit_media.py`, `audit_media_sizes.py`: проверка целостности файлов на физических носителях.
- `generate_audit_report.py`, `generate_overview.py`: формирование сводных отчетов по коллекции.
- `perform_migration_safe.py`, `update_db.py`, `update_db_schema.py`: миграции и обновление структуры `media.db`.
- `delete_corrupted_paths.py`, `dry_run_duplicates.py`, `find_cross_dir_duplicates.py`: поиск и удаление дубликатов.\n