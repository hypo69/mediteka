# Краткая сводка по скриптам

*Обновлено: 2026-07-25 13:41*


## Анализ и отчетность (3)

- `analyze_completed.py` - Python (63 строк)
- `analyze_duplicates.py` - Python (60 строк)
- `analyze_media_data.py` - Python (39 строк)

## Работа с торрентами (8)

- `assign_categories_to_torrents.py` - Python (105 строк)
- `assign_torrents_ids.py` - Python (120 строк)
- `clear_torrents_meta.py` - Python (86 строк)
- `force_update_torrents.py` - Python (60 строк)
- `orchestrator_torrent.py` - Python (44 строк)
- `run_assign_torrents.py` - Python (46 строк)
- `update_torrent_state.py` - Python (76 строк)
- `update_torrents_path.py` - Python (94 строк)

## Обработка медиатеки (13)

- `audit_and_update_db.py` - Python (63 строк)
- `audit_disk.py` - Python (114 строк)
- `audit_media.py` - Python (79 строк)
- `audit_media_sizes.py` - Python (63 строк)
- `audit_poirot_v2.py` - Python (48 строк)
- `complete_media_data.py` - Python (44 строк)
- `fill_missing_metadata.py` - Python (148 строк)
- `generate_audit_report.py` - Python (25 строк)
- `generate_deletion_candidates.py` - Python (51 строк)
- `generate_inferred_titles.py` - Python (38 строк)
- `generate_overview.py` - Python (310 строк)
- `generate_reports.py` - Python (54 строк)
- `update_media_sizes.py` - Python (120 строк)

## Основные Launch-скрипты (9)

- `bot_runner.py` - Python (89 строк)
- `install.ps1` - PowerShell (4,823 байт)
- `install_ssl_cert.ps1` - PowerShell (1,856 байт)
- `main.py` - Python (278 строк)
- `Run-Cloudflared.ps1` - PowerShell (4,363 байт)
- `Run-Engrock.ps1` - PowerShell (6,644 байт)
- `Run-Foundry.ps1` - PowerShell (6,289 байт)
- `Run-Unicorn.ps1` - PowerShell (5,839 байт)
- `run.ps1` - PowerShell (8,775 байт)

## Проверки и диагностика (10)

- `check_db.py` - Python (23 строк)
- `check_db_data.py` - Python (36 строк)
- `check_db_paths.py` - Python (9 строк)
- `check_empty_title_ru.py` - Python (17 строк)
- `check_media_type.py` - Python (17 строк)
- `check_poirot_remaining.py` - Python (11 строк)
- `check_remaining.py` - Python (12 строк)
- `check_walker.py` - Python (11 строк)
- `debug_qbt.py` - Python (27 строк)
- `debug_qbt_list.py` - Python (27 строк)

## Прочие скрипты (23)

- `convert_to_md.py` - Python (39 строк)
- `delete_corrupted_paths.py` - Python (10 строк)
- `delete_poirot_non_hd.py` - Python (33 строк)
- `delete_source_folders.py` - Python (63 строк)
- `dry_run_duplicates.py` - Python (50 строк)
- `enrich_incomplete_records.py` - Python (76 строк)
- `find_cross_dir_duplicates.py` - Python (29 строк)
- `find_incomplete_records.py` - Python (52 строк)
- `find_target_deletion_candidates.py` - Python (20 строк)
- `get_media_card.py` - Python (57 строк)
- `get_remaining_non_hd_ids.py` - Python (11 строк)
- `header.py` - Python (41 строк)
- `identify_poirot_to_delete.py` - Python (35 строк)
- `import_missing_media.py` - Python (46 строк)
- `insert_storage_data.py` - Python (71 строк)
- `inspect_user_rags.py` - Python (23 строк)
- `list_duplicates.py` - Python (22 строк)
- `package_skill.py` - Python (38 строк)
- `rebuild_rag.py` - Python (24 строк)
- `refine_deletions.py` - Python (39 строк)
- `run_dry_run.py` - Python (39 строк)
- `update_specific_drives_sizes.py` - Python (52 строк)
- `view_storage.py` - Python (26 строк)

## Статистика и подсчет (3)

- `count_media.py` - Python (14 строк)
- `count_media_by_category.py` - Python (23 строк)
- `count_remaining.py` - Python (10 строк)

## Работа с БД (4)

- `get_schema.py` - Python (9 строк)
- `remove_columns.py` - Python (40 строк)
- `update_db.py` - Python (96 строк)
- `update_db_schema.py` - Python (28 строк)

## CLI Управление и утилиты (3)

- `manage_knowledge.py` - Python (367 строк)
- `manage_tools.py` - Python (293 строк)
- `run_media_organizer.py` - Python (282 строк)

## Миграции и бэкапы (3)

- `perform_migration.py` - Python (194 строк)
- `perform_migration_safe.py` - Python (158 строк)
- `simulate_migration.py` - Python (89 строк)