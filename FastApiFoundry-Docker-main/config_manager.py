# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Унифицированный класс конфигурации
# =============================================================================
# Описание:
#   Класс Config для всего проекта FastApiFoundry.
#   Загружает настройки из config.json и предоставляет единый интерфейс доступа.
#
# File: config_manager.py
# Project: Ai Assistant (Docker)
# Version: 0.8.0
# Изменения в 0.6.1:
#   - Полная русификация документации
#   - Добавлены строгие аннотации типов возвращаемых значений
#   - Комментарии к проверкам `if` в стиле "Проверка ..."
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class Config:
    """Единый класс конфигурации для всего проекта."""

    _instance = None
    _config_data: Dict[str, Any] = {}
    _foundry_base_url = None  # Dynamically set in run.py

    def __new__(cls):
        if cls._instance is None: # Проверка существования экземпляра (Singleton)
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
            # Инициализация необходимых директорий
            # Initialization of required directories
            cls._instance._ensure_dirs()
        return cls._instance

    def _ensure_dirs(self) -> None:
        """Создание необходимых директорий проекта.
        
        Обоснование:
          - Гарантированное наличие папок logs и archive в ~/.aiassistant/.
          - Автоматическое создание при первом запуске (инициализация/инсталляция).
        """
        for path in (
            Path('~/.aiassistant/logs').expanduser(),
            Path('~/.aiassistant/archive').expanduser(),
            Path('~/.aiassistant/dialogs').expanduser(),
        ):
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    logger.error(f"❌ Ошибка создания директории {path}: {e}")

    def _load_config(self) -> None:
        """Загрузка конфигурации из файла config.json.

        Raises:
            FileNotFoundError: If config.json does not exist.
            json.JSONDecodeError: If config.json contains invalid JSON.
            OSError: If config.json cannot be read (permissions, lock).
        """
        config_path = Path('config.json')

        if not config_path.is_file(): # Проверка наличия файла конфигурации
            # Файл отсутствует — запуск невозможен; выбрасываем исключение
            raise FileNotFoundError(f'Файл config.json не найден: {config_path.absolute()}')

        _quiet = os.getenv('_UVICORN_CHILD') == '1'
        if not _quiet: # Проверка необходимости вывода логов загрузки
            print(f'Загрузка конфигурации: {config_path.absolute()}')

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
            if not _quiet: # Проверка вывода структуры секций
                print(f'Конфигурация загружена, секции: {list(self._config_data.keys())}')
        except json.JSONDecodeError as e:
            # Ошибка парсинга JSON — логируем и выбрасываем исключение
            logger.error(f'❌ config.json содержит некорректный JSON: {e}')
            raise
        except OSError as e:
            logger.error(f'❌ Не удалось прочитать config.json: {e}')
            raise

    def reload_config(self) -> None:
        """Перезагрузка конфигурации с диска.

        Raises:
            FileNotFoundError: If config.json does not exist.
            json.JSONDecodeError: If config.json contains invalid JSON.
            OSError: If config.json cannot be read.
        """
        self._load_config()

    # ── Сервер FastAPI ────────────────────────────────────────────────────

    @property
    def api_host(self) -> str:
        return self._config_data.get('fastapi_server', {}).get('host') or '0.0.0.0'

    @property
    def api_port(self) -> int:
        return self._config_data.get('fastapi_server', {}).get('port') or 9696

    @property
    def api_workers(self) -> int:
        return self._config_data.get('fastapi_server', {}).get('workers') or 1

    @property
    def api_reload(self) -> bool:
        return self._config_data.get('fastapi_server', {}).get('reload', True)

    @property
    def api_log_level(self) -> str:
        return self._config_data.get('fastapi_server', {}).get('log_level', 'INFO')

    # ── Логирование ───────────────────────────────────────────────────────

    @property
    def logging_retention_hours(self) -> int:
        return self._config_data.get('logging', {}).get('retention_hours') or 24

    @property
    def history_retention_days(self) -> int:
        return self._config_data.get('logging', {}).get('history_retention_days') or 7

    @property
    def archive_max_size_gb(self) -> int:
        return self._config_data.get('logging', {}).get('archive_max_size_gb') or 2

    @property
    def archive_keep_files(self) -> List[str]:
        return self._config_data.get('logging', {}).get('archive_keep_files') or []

    # ── Telegram Admin Bot ────────────────────────────────────────────────

    @property
    def telegram_admin_token(self) -> str:
        """Token for admin_bot. Env: TELEGRAM_ADMIN_TOKEN."""
        return os.getenv('TELEGRAM_ADMIN_TOKEN', '')

    @property
    def telegram_admin_ids(self) -> List[int]:
        """Allowed admin user IDs. Env: TELEGRAM_ADMIN_IDS (comma-separated)."""
        raw = os.getenv('TELEGRAM_ADMIN_IDS', '')
        if raw:
            try:
                return [int(x.strip()) for x in raw.split(',') if x.strip()]
            except ValueError:
                pass
        return self._config_data.get('telegram', {}).get('allowed_external_ids', [])

    @property
    def telegram_status_check_interval(self) -> int:
        return self._config_data.get('telegram', {}).get('status_check_interval', 300)

    # ── Telegram HelpDesk Bot ─────────────────────────────────────────────

    @property
    def telegram_helpdesk_token(self) -> str:
        """Token for helpdesk_bot. Env: TELEGRAM_HELPDESK_TOKEN."""
        return os.getenv('TELEGRAM_HELPDESK_TOKEN', '')

    @property
    def telegram_listener_token(self) -> str:
        """Token for listener_bot. Env: TELEGRAM_LISTENER_TOKEN."""
        return os.getenv('TELEGRAM_LISTENER_TOKEN', '')

    @property
    def telegram_helpdesk_rag_profile(self) -> str:
        """RAG profile used by helpdesk_bot."""
        return self._config_data.get('telegram_helpdesk', {}).get('rag_profile', 'support')

    # ── Telegram legacy aliases (backward compat) ─────────────────────────

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_admin_token)

    @property
    def telegram_token(self) -> str:
        """Deprecated: use telegram_admin_token."""
        return self.telegram_admin_token

    @property
    def telegram_allowed_ids(self) -> List[int]:
        """Deprecated: use telegram_admin_ids."""
        return self.telegram_admin_ids

    @property
    def telegram_chat_history_enabled(self) -> bool:
        return self._config_data.get('telegram', {}).get('chat_history_enabled', True)

    @property
    def telegram_chat_history_file(self) -> str:
        return self._config_data.get('telegram', {}).get('chat_history_file', 'session_history.json')

    @property
    def telegram_support_token(self) -> str:
        """Deprecated: use telegram_helpdesk_token."""
        return self.telegram_helpdesk_token

    @property
    def telegram_support_rag_profile(self) -> str:
        """Deprecated: use telegram_helpdesk_rag_profile."""
        return self.telegram_helpdesk_rag_profile

    # ── Model Manager (LRU / TTL / RAM guard) ──────────────────────────────

    @property
    def model_manager_max_loaded(self) -> int:
        """Max models loaded in Foundry simultaneously before LRU eviction."""
        return self._config_data.get('model_manager', {}).get('max_loaded_models', 1)

    @property
    def model_manager_ttl_seconds(self) -> int:
        """Seconds of inactivity before a model is unloaded."""
        return self._config_data.get('model_manager', {}).get('ttl_seconds', 600)

    @property
    def model_manager_max_ram_percent(self) -> float:
        """RAM usage threshold (%) above which LRU eviction is triggered."""
        return self._config_data.get('model_manager', {}).get('max_ram_percent', 80.0)

    # ── ИИ Foundry ────────────────────────────────────────────────────────

    @property
    def foundry_base_url(self) -> str:
        # Runtime override (set by run.py after discovery) takes priority.
        # Falls back to static value from config.json.
        if self._foundry_base_url:
            return self._foundry_base_url
        return self._config_data.get('foundry_ai', {}).get('base_url', '') or ''

    @foundry_base_url.setter
    def foundry_base_url(self, value: str) -> None:
        self._foundry_base_url = value

    @property
    def foundry_port(self) -> int:
        """Порт Foundry сервиса из base_url или из конфига."""
        base_url = self.foundry_base_url
        if base_url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                if parsed.port:
                    return parsed.port
            except (ValueError, AttributeError):
                pass
        # Fallback to config value or default
        return self._config_data.get('foundry_ai', {}).get('port', 63995)

    @property
    def foundry_default_model(self) -> str:
        return self._config_data.get('foundry_ai', {}).get('default_model', '')

    @property
    def foundry_auto_start(self) -> bool:
        return self._config_data.get('foundry_ai', {}).get('auto_start', True)

    @property
    def foundry_auto_load_default(self) -> bool:
        return self._config_data.get('foundry_ai', {}).get('auto_load_default', False)

    @property
    def foundry_startup_models(self) -> List[str]:
        models = self._config_data.get('foundry_ai', {}).get('startup_models', [])
        if isinstance(models, str):
            return [models] if models.strip() else []
        return [str(m) for m in models if str(m).strip()]

    @property
    def foundry_temperature(self) -> float:
        return self._config_data.get('foundry_ai', {}).get('temperature', 0.7)

    @property
    def huggingface_auto_load_default(self) -> bool:
        """Whether to auto-load HuggingFace model at startup.

        Priority: HF_AUTO_LOAD_DEFAULT env → config.json → default True.
        Validates that value is boolean, logs error and uses default if invalid.
        """
        # Check environment variable first
        env_value = os.getenv('HF_AUTO_LOAD_DEFAULT')
        if env_value is not None:
            try:
                return env_value.lower() in ('true', '1', 'yes')
            except AttributeError:
                logger.error(f'❌ Invalid HF_AUTO_LOAD_DEFAULT value: {env_value}. Using default True.')
                return True

        # Check config.json
        config_value = self._config_data.get('huggingface', {}).get('auto_load_default')
        if config_value is not None:
            if isinstance(config_value, bool):
                return config_value
            else:
                logger.error(f'❌ Invalid huggingface.auto_load_default value: {config_value}. Using default True.')
                return True

        # Default value
        return True

    @property
    def foundry_top_p(self) -> float:
        return self._config_data.get('foundry_ai', {}).get('top_p', 0.9)

    @property
    def foundry_top_k(self) -> int:
        return self._config_data.get('foundry_ai', {}).get('top_k', 50)

    @property
    def foundry_models_dir(self) -> str:
        raw = self._config_data.get('foundry_ai', {}).get('models_dir') or '~/.foundry/cache/models'
        return str(Path(raw).expanduser())

    # ── llama.cpp ──────────────────────────────────────────────────────────────────────

    @property
    def llama_models_dir(self) -> str:
        raw = (
            self._config_data.get('llama_cpp', {}).get('models_dir')
            or self._config_data.get('directories', {}).get('models')
            or '~/.models'
        )
        return str(Path(raw).expanduser())

    @property
    def llama_model_path(self) -> str:
        """Full path to default llama.cpp model: models_dir / default_model."""
        default_model = self._config_data.get('llama_cpp', {}).get('default_model', '')
        if not default_model:
            return ''
        p = Path(default_model)
        if p.is_absolute():
            return str(p)
        return str(Path(self.llama_models_dir) / default_model)

    # ── LM Studio ─────────────────────────────────────────────────────────

    @property
    def lmstudio_base_url(self) -> str:
        return os.getenv('LMSTUDIO_BASE_URL', '') or self._config_data.get('lmstudio', {}).get('base_url', 'http://localhost:1234')

    @property
    def lmstudio_api_key(self) -> str:
        return os.getenv('LMSTUDIO_API_KEY', '') or self._config_data.get('lmstudio', {}).get('api_key', '')

    @property
    def lmstudio_default_model(self) -> str:
        return os.getenv('LMSTUDIO_DEFAULT_MODEL', '') or self._config_data.get('lmstudio', {}).get('default_model', '')

    @property
    def lmstudio_request_timeout_sec(self) -> int:
        return self._config_data.get('lmstudio', {}).get('request_timeout_sec', 300)

    # ── Управление портами ────────────────────────────────────────────────

    @property
    def port_auto_find_free(self) -> bool:
        return self._config_data.get('port_management', {}).get('auto_find_free_port', False)

    @property
    def port_range_start(self) -> int:
        return self._config_data.get('port_management', {}).get('port_range_start', 8000)

    @property
    def port_range_end(self) -> int:
        return self._config_data.get('port_management', {}).get('port_range_end', 8100)

    # ── Система RAG ───────────────────────────────────────────────────────

    @property
    def rag_enabled(self) -> bool:
        return self._config_data.get('rag_system', {}).get('enabled', False)

    @property
    def rag_index_dir(self) -> str:
        raw = self._config_data.get('rag_system', {}).get('index_dir') or '~/.rag/default_index'
        return str(Path(raw).expanduser())

    @property
    def rag_model(self) -> str:
        return self._config_data.get('rag_system', {}).get('model', 'sentence-transformers/all-MiniLM-L6-v2')

    @property
    def rag_chunk_size(self) -> int:
        return self._config_data.get('rag_system', {}).get('chunk_size', 1000)

    @property
    def rag_top_k(self) -> int:
        return self._config_data.get('rag_system', {}).get('top_k', 5)

    # ── Директории ────────────────────────────────────────────────────────

    @property
    def dir_models(self) -> str:
        raw = self._config_data.get('directories', {}).get('models') or '~/.models'
        return str(Path(raw).expanduser())

    @property
    def dir_rag(self) -> str:
        raw = self._config_data.get('directories', {}).get('rag') or '~/.rag'
        return str(Path(raw).expanduser())

    @property
    def dir_hf_models(self) -> str:
        raw = self._config_data.get('directories', {}).get('hf_models') or '~/.cache/huggingface/hub'
        return str(Path(raw).expanduser())

    @property
    def dir_dialogs(self) -> str:
        """Directory for storing all dialog history files.

        Returns:
            str: Absolute path to dialogs directory (expanded ~).
        """
        raw = self._config_data.get('dialogs', {}).get('dir') or '~/.aiassistant/dialogs'
        return str(Path(raw).expanduser())

    @property
    def dialogs_retention_days(self) -> int:
        """Number of days to keep dialog files before cleanup.

        Returns:
            int: Retention period in days.
        """
        return self._config_data.get('dialogs', {}).get('retention_days') or 30

    @property
    def dialogs_max_size_mb(self) -> int:
        """Maximum total size of dialogs directory in MB.

        Returns:
            int: Size limit in megabytes.
        """
        return self._config_data.get('dialogs', {}).get('max_size_mb') or 100

    # ── История чатов (SQLite) ────────────────────────────────────────────

    @property
    def chat_history_db_path(self) -> str:
        """Путь к SQLite-базе истории чатов (с раскрытием ~).

        Returns:
            str: Абсолютный путь к файлу базы данных.
        """
        from pathlib import Path
        raw = self._config_data.get('chat_history', {}).get('db_path') or '~/.aiassistant/chat/history/chat_history.db'
        return str(Path(raw).expanduser())

    @property
    def chat_history_retention_days(self) -> int:
        """Количество дней хранения истории чатов.

        Returns:
            int: Срок хранения в днях.
        """
        return self._config_data.get('chat_history', {}).get('retention_days', 90)

    @property
    def chat_history_max_sessions(self) -> int:
        """Максимальное количество хранимых сессий.

        Returns:
            int: Лимит сессий.
        """
        return self._config_data.get('chat_history', {}).get('max_sessions', 10000)

    @property
    def chat_history_rag_auto_ingest(self) -> bool:
        """Автоматическое добавление истории чатов в RAG-индекс.

        Returns:
            bool: True если автоиндексация включена.
        """
        return self._config_data.get('chat_history', {}).get('rag_auto_ingest', False)

    # ── Помощники ─────────────────────────────────────────────────────────

    def get_section(self, section: str) -> Dict[str, Any]:
        """Получение всей секции конфигурации целиком.

        Args:
            section (str): Название секции (например, 'fastapi_server').

        Returns:
            Dict[str, Any]: Содержимое секции или пустой словарь.
        """
        return self._config_data.get(section, {})

    def get_raw_config(self) -> Dict[str, Any]:
        """Получение копии всей конфигурации.

        Returns:
            Dict[str, Any]: Полное содержимое config.json в виде словаря.
        """
        return self._config_data.copy()

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Обновление конфигурации в памяти и сохранение в файл config.json.

        Args:
            new_config (Dict[str, Any]): Новый словарь настроек.

        Raises:
            OSError: При ошибке записи на диск.
        """
        self._config_data = new_config
        config_path = Path('config.json')
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=2, ensure_ascii=False)
        except OSError as e:
            # Запись на диск не удалась — настройки обновлены в памяти, но не сохранены
            logger.error(f'❌ Не удалось записать в config.json: {e}')
            raise


# Global configuration instance
config = Config()
