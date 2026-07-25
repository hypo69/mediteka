# Smart Torrent Storage Management

Модуль `Smart Torrent Storage Management` предоставляет интеллектуальное управление свободным местом на дисках медиатеки, автоматическую предзагрузку сериалов на основе активности пользователей и интерактивную очистку дисков.

---

## Архитектура системы

Система состоит из пяти основных компонентов, взаимодействующих через SQLite БД (`media.db`) и Web API клиента qBittorrent:

```
[User Watch History] -> [WatchActivityDetector] 
                              |
                              v (actively watched status)
[DiskQuotaManager]   -> [TorrentPrefetchAgent]  -> [qBittorrent Client]
                              |
                              v (retention / purge)
                        [TorrentRetentionAgent] & [InteractiveRetentionAgent]
```

---

## Компоненты

### 1. Менеджер квот (`DiskQuotaManager`)
Модуль [disk_quota_manager.py](file:///C:/mediateka/plugins/media_organizer/core/disk_quota_manager.py) отвечает за мониторинг физических накопителей и расчет логических зон:
* **70% Хранилище (Archive/Storage)**: Постоянное место для фильмов и сохраненных 1-х сезонов сериалов.
* **25% Буфер загрузок (Active Downloads)**: Временное место для активных фоновых закачек.
* **5% Неприкосновенный запас (Emergency Reserve)**: Предохранительный буфер. Если свободное место падает ниже 5%, все новые загрузки блокируются.

### 2. Детектор просмотров (`WatchActivityDetector`)
Модуль [watch_activity_detector.py](file:///C:/mediateka/plugins/media_organizer/core/watch_activity_detector.py) анализирует историю проигрывания:
* Читает историю из персональных JSON-профилей пользователей (`user_profile_*.json`).
* Если в 1-м сезоне сериала просмотрено **не менее 3 серий** (с прогрессом воспроизведения > 50% или флагом `completed`), сериал получает статус `actively_watched`.

### 3. Автоматический агент очистки (`TorrentRetentionAgent`)
Модуль [torrent_retention_agent.py](file:///C:/mediateka/plugins/media_organizer/core/torrent_retention_agent.py) чистит неактивные сериалы:
* Для сериалов без статуса `actively_watched` находит все серии сезонов > 1.
* Физически удаляет файлы этих серий с диска и из БД.
* Устанавливает приоритет этих файлов в qBittorrent в значение `0` ("Do Not Download"), сохраняя раздачу в клиенте без лишнего расхода диска.
* Сохраняет пилотную серию и весь первый сезон.

### 4. Агент фоновой предзагрузки (`TorrentPrefetchAgent`)
Модуль [torrent_prefetch_agent.py](file:///C:/mediateka/plugins/media_organizer/core/torrent_prefetch_agent.py) скачивает продолжение:
* Для сериалов со статусом `actively_watched` автоматически переводит файлы последующих сезонов (сезон 2 и далее) из статуса "Do Not Download" в приоритет "Normal" (1).
* Проверяет доступный лимит диска перед стартом новых закачек.

### 5. Интерактивный агент очистки (`InteractiveRetentionAgent`)
Модуль [interactive_retention_agent.py](file:///C:/mediateka/plugins/media_organizer/core/interactive_retention_agent.py) готовит кандидатов на удаление:
* Ищет сериалы/фильмы, которые:
  1. Полностью просмотрены (`completed = True` на всех сериях).
  2. Не просматривались более 30 дней.
  3. Брошены на середине (не просматривались > 30 дней, но не завершены).
* Позволяет администраторам подтвердить очистку через интерфейс Telegram.

---

## Интеграция с Telegram-ботом

В Telegram-боте реализована интерактивная команда управления дисками:
* **/clean** — Доступна только для пользователей с ролью `admin` в базе данных. Выводит интерактивный список кандидатов на очистку с размером файлов на диске и причиной удаления (например, "Брошено на середине").
* При нажатии inline-кнопки `🗑️ Удалить <Название>` бот обращается к `InteractiveRetentionAgent`, удаляет файлы, отключает закачку в qBittorrent и высылает отчет об освобожденном месте.
* Кнопка `❌ Отменить` прерывает процесс очистки.

---

## Тестирование и запуск

Для проверки работоспособности всех компонентов в режиме симуляции (Dry Run) используйте проверочный скрипт:
```bash
python C:\Users\onela\.gemini\antigravity\brain\7d720ae6-430a-4f08-b0bd-aaceeef327ea\scratch\test_smart_retention.py
```
Скрипт проверяет дисковые лимиты, считывает профили, опрашивает qBittorrent API и имитирует шаги очистки и предзагрузки без изменения файлов.
