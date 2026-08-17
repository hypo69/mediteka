# Модуль `plugins.qbittorrent` — Интеграция с qBittorrent

## Назначение
Плагин обеспечивает взаимодействие с торрент-клиентом qBittorrent через Web API:
- `qbittorrent.py`: реализация плагина `QBittorrentPlugin` и API-клиента.
- `config.json`: параметры подключения к qBittorrent Web UI.
- `tools/`: утилиты синхронизации, разметки категорий и оркестрации.
- `torrent_files/`: локальное хранилище `.torrent` файлов.\n