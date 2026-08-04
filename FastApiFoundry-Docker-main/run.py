#!/usr/bin/env python311
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Запуск сервера FastApiFoundry
# =============================================================================
# Описание:
#   Упрощенный запуск сервера FastAPI.
#   Если Foundry уже запущен, функции ИИ будут доступны автоматически.
#   Для полного запуска со всеми зависимостями используйте start.ps1.
#
# File: run.py
# Project: Ai Assistant (Docker)
# Package: FastApiFoundry
# Version: 0.6.1
# Author: hypo69
# Module: run
# Copyright: © 2026 hypo69
# License: MIT
# Date: 2025
# =============================================================================

# FORCED UTF-8 ENCODING SETUP
import os
import sys
import shutil
import time
from datetime import datetime
import locale
from typing import Optional

# Forced UTF-8 encoding setup for the entire Python process
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32': # Windows platform check
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
        pass  # Check: if encoding is already set
    # Attempt to set UTF-8 locale
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except:
            pass  # Check: use system default locale

import json
import socket
import logging
from pathlib import Path

# Adding current directory to sys.path for module imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path: # Check if path is in sys.path
    sys.path.insert(0, str(current_dir))

# Добавление site-packages для python311
# Проверка: добавлять только если путь существует и это Windows
if sys.platform == 'win32' and Path('C:/python311/Lib/site-packages').exists(): 
    sys.path.append('C:/python311/Lib/site-packages')

# Загрузка переменных окружения перед импортом конфигурации
# Проверка: защита от двойного выполнения в режиме перезагрузки uvicorn
_in_reloader_child = os.getenv('_UVICORN_CHILD') == '1'
if not _in_reloader_child:
    os.environ['_UVICORN_CHILD'] = '1'

try:
    from src.utils.env_processor import load_env_variables, process_config
    load_env_variables()
except ImportError:
    pass

from src.core.config import config

# Импорт зависимостей и инициализация логирования
from src.logger import logger as _root_logger
from src.utils.logging_config import setup_logging
setup_logging(os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    logger.warning("Библиотека requests недоступна, некоторые функции отключены")
    REQUESTS_AVAILABLE = False

try:
    import uvicorn
except ImportError:
    logger.error("Библиотека uvicorn недоступна, запуск сервера невозможен")
    sys.exit(1)


# =============================================================================
# Утилиты
# =============================================================================
def find_free_port(start_port: int = 9696, end_port: int = 9796) -> Optional[int]:
    """Поиск свободного порта в заданном диапазоне.

    Args:
        start_port (int): Начальный порт диапазона. По умолчанию 9696.
        end_port (int): Конечный порт диапазона. По умолчанию 9796.

    Returns:
        Optional[int]: Номер свободного порта или None, если порты заняты.

    Raises:
        OSError: При системных ошибках работы с сокетами.
    """
    port: int = 0

    logger.debug(f"Поиск свободного порта в диапазоне {start_port}-{end_port}")
    
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(('localhost', port))
                logger.info(f"Найден свободный порт: {port}")
                return port
            except OSError:
                logger.debug(f"Порт {port} занят")
                continue
    
    logger.warning(f"Не удалось найти свободный порт в диапазоне {start_port}-{end_port}")
    return None


def cleanup_log_temp_files(log_dir: Path) -> None:
    """Очистка временных файлов в директории логов.

    ПОЧЕМУ ВЫБРАНО ЭТО РЕШЕНИЕ:
      - Использование `pathlib.glob` обеспечивает эффективный поиск файлов по маске.
      - Проверка времени изменения (`st_mtime`) предотвращает удаление активных временных файлов.
      - Обработка исключений внутри цикла предотвращает остановку процесса при блокировке отдельных файлов.
      - Вызов функции при старте гарантирует чистоту рабочего окружения.

    Args:
        log_dir (Path): Путь к директории с логами.
    """
    temp_files: list[Path] = []
    file_path: Path = None
    current_time: float = time.time()
    # Получение периода хранения из конфигурации (в часах) и перевод в секунды
    # Retrieval of retention period from config (hours) and conversion to seconds
    retention_period_seconds: int = config.logging_retention_hours * 3600
    file_mtime: float = 0.0
    archive_dir: Path = log_dir.parent / "archive"

    # Проверка существования директории для исключения ошибок пути
    # Directory existence check to prevent errors on non-existent path
    if not log_dir.exists():
        return

    logger.info(f"Очистка устаревших временных файлов в {log_dir}...")
    
    # Поиск всех файлов с расширением .tmp
    # Search for all files with .tmp extension
    temp_files = list(log_dir.glob("*.tmp"))
    
    for file_path in temp_files:
        try:
            # Получение времени последнего изменения
            # Retrieval of the last modification time
            file_mtime = file_path.stat().st_mtime
            
            # Проверка возраста файла (удаление только старше 24 часов)
            # Verification of file age (deletion only older than 24 hours)
            if (current_time - file_mtime) > retention_period_seconds:
                # Обеспечение наличия директории архива
                # Ensuring archive directory existence
                if not archive_dir.exists():
                    archive_dir.mkdir(parents=True, exist_ok=True)

                # Формирование имени в архиве с меткой времени
                # Generation of archive filename with a timestamp
                timestamp = datetime.fromtimestamp(file_mtime).strftime("%Y%m%d_%H%M%S")
                archive_name = f"{file_path.stem}_{timestamp}.tmp"
                archive_file = archive_dir / archive_name

                # Перемещение файла в архив (архивация перед удалением из logs)
                # Moving file to archive (archiving before removal from logs)
                shutil.move(str(file_path), str(archive_file))
                logger.debug(f"Архивация временного файла: {file_path.name} -> {archive_name}")
        except Exception as e:
            logger.warning(f"Ошибка при архивации файла {file_path.name}: {e}")


def cleanup_session_history(archive_dir: Path) -> None:
    """Ротация файла истории чата при превышении срока хранения.

    Обоснование:
      - Предотвращение накопления данных в корне проекта.
      - Сохранение старых сессий в архив вместо безвозвратного удаления.

    Args:
        archive_dir (Path): Директория архива (~/.ai-assist/archive).
    """
    dialogs_dir: Path = Path('~/.ai-assist/dialogs').expanduser()
    history_file: Path = dialogs_dir / 'session_history.json'
    retention_seconds: int = config.history_retention_days * 86400
    current_time: float = time.time()
    file_mtime: float = 0.0

    if not history_file.exists():
        return

    try:
        file_mtime = history_file.stat().st_mtime

        if (current_time - file_mtime) > retention_seconds:
            if not archive_dir.exists():
                archive_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.fromtimestamp(file_mtime).strftime("%Y%m%d_%H%M%S")
            archive_name = f"session_history_{timestamp}.json"
            archive_file = archive_dir / archive_name

            shutil.move(str(history_file), str(archive_file))
            logger.info(f"Выполнена ротация истории сессии: {archive_file.name}")
    except Exception as e:
        logger.warning(f"Не удалось выполнить ротацию файла истории сессии: {e}")


def cleanup_archive_size(archive_dir: Path) -> None:
    """Очистка папки archive при превышении лимита размера.

    ПОЧЕМУ ВЫБРАНО ЭТО РЕШЕНИЕ:
      - Предотвращение бесконтрольного роста архива на диске.
      - Удаление в первую очередь самых старых файлов (FIFO).
      - Использование конфигурационного лимита (по умолчанию 2 ГБ).

    Args:
        archive_dir (Path): Директория архива (~/.aiassistant/archive).
    """
    archive_dir: Path = archive_dir
    max_size_bytes: int = config.archive_max_size_gb * 1024 * 1024 * 1024
    current_total_size: int = 0
    archived_files: list[Path] = []
    keep_files: List[str] = config.archive_keep_files
    file_path: Path = None

    if not archive_dir.exists():
        return

    # Получение списка файлов, отсортированных по времени изменения (от старых к новым)
    # Retrieval of the file list sorted by modification time (old to new)
    archived_files = sorted(
        [f for f in archive_dir.glob("*") if f.is_file() and f.name not in keep_files],
        key=lambda x: x.stat().st_mtime
    )

    # Подсчет текущего общего размера
    # Calculation of the current total size
    current_total_size = sum(f.stat().st_size for f in archived_files)

    if current_total_size <= max_size_bytes:
        return

    logger.info(f"Превышен лимит папки archive ({current_total_size / 1024 / 1024:.2f} MB). Очистка...")

    for file_path in archived_files:
        if current_total_size <= max_size_bytes:
            break
        
        try:
            file_size = file_path.stat().st_size
            file_path.unlink()
            current_total_size -= file_size
            logger.debug(f"Удален старый архивный файл: {file_path.name}")
        except Exception as e:
            logger.warning(f"Ошибка при удалении архивного файла {file_path.name}: {e}")


# =============================================================================
# Управление портами
# =============================================================================
def get_server_port() -> int:
    """Определение порта для запуска сервера FastAPI.

    Returns:
        int: Номер порта для сервера.
    """
    default_port: int = config.api_port
    auto_find: bool = False
    start_port: int = 0
    end_port: int = 0
    free_port: Optional[int] = None
    auto_find = config.port_auto_find_free
    
    logger.info(f"Определение порта сервера FastAPI...")
    logger.debug(f"Порт по умолчанию: {default_port}")
    logger.debug(f"Автоматический поиск порта: {auto_find}")

    if not auto_find: # Проверка: если автопоиск отключен, используем фиксированный порт
        logger.info(f'Использование фиксированного порта: {default_port}')
        return default_port

    start_port = config.port_range_start
    end_port = config.port_range_end

    free_port = find_free_port(start_port, end_port)
    if free_port: # Проверка: если свободный порт найден
        logger.info(f'Найден свободный порт: {free_port}')
        return free_port

    logger.warning(f'Свободный порт не найден, используется порт по умолчанию {default_port}')
    return default_port


# =============================================================================
# Foundry
# =============================================================================
def find_foundry_port() -> Optional[int]:
    """Поиск порта работающего сервиса Foundry.

    Returns:
        Optional[int]: Номер порта Foundry или None, если сервис не найден.
    """
    from src.utils.foundry_utils import find_foundry_port as _find_port
    return _find_port()


def resolve_foundry_base_url() -> Optional[str]:
    """Определение базового URL для Foundry.

    Приоритет:
    1. Переменная окружения FOUNDRY_BASE_URL
    2. Переменная окружения FOUNDRY_DYNAMIC_PORT
    3. Конфигурация config.json (foundry_ai.base_url)

    Returns:
        Optional[str]: Полный URL сервиса Foundry или None.
    """
    foundry_url: Optional[str] = None
    foundry_port_env: Optional[str] = None
    port: int = 0

    # Проверка переменной окружения FOUNDRY_BASE_URL
    foundry_url = os.getenv('FOUNDRY_BASE_URL')
    if foundry_url: # Проверка: если URL задан явно
        logger.info(f'Foundry найден через переменную окружения: {foundry_url}')
        return foundry_url
    
    # Проверка устаревшей переменной FOUNDRY_DYNAMIC_PORT
    foundry_port_env = os.getenv('FOUNDRY_DYNAMIC_PORT')
    if foundry_port_env: # Проверка наличия порта в окружении
        try:
            port = int(foundry_port_env)
            foundry_url = f'http://localhost:{port}/v1/'
            logger.info(f'Foundry найден через системную переменную порта: {foundry_url}')
            return foundry_url
        except ValueError:
            pass
    
    # Использование URL из конфигурации
    from src.core.config import config
    foundry_url = config.foundry_base_url
    if foundry_url:
        logger.info(f'Foundry найден через конфигурацию: {foundry_url}')
        return foundry_url

    logger.warning('Foundry не настроен в config.json')
    return None


def check_foundry(foundry_base_url: Optional[str]) -> bool:
    """Проверка доступности Foundry API по HTTP.

    Args:
        foundry_base_url (Optional[str]): Базовый URL для проверки.

    Returns:
        bool: True, если API ответило кодом 200.
    """
    response = None

    if not foundry_base_url or not REQUESTS_AVAILABLE: # Проверка входных данных и зависимостей
        return False

    try:
        response = requests.get(
            f'{foundry_base_url}models',
            timeout=3,
        )
        return response.status_code == 200 # Проверка успешности HTTP запроса
    except Exception:
        return False


# =============================================================================
# Основная функция
# =============================================================================
def main() -> bool:
    """Главная функция инициализации и запуска сервера.

    Returns:
        bool: True при успешном запуске и работе сервера.
    """
    foundry_base_url: Optional[str] = None
    log_dir: Path = Path('~/.ai-assist/logs').expanduser()
    archive_dir: Path = Path('~/.ai-assist/archive').expanduser()
    host: str = ""
    reload_enabled: bool = False
    log_level: str = ""
    workers: int = 1
    port: int = 0

    try:
        logger.info('FastAPI Foundry')
        logger.info('=' * 50)

        # -------------------------------------------------------------------------
        # Очистка временных ресурсов
        # -------------------------------------------------------------------------
        # Удаление устаревших временных файлов логов для предотвращения засорения диска
        # Cleanup of temporary log files on startup to prevent disk clutter
        cleanup_log_temp_files(log_dir)
        cleanup_session_history(archive_dir)
        cleanup_archive_size(archive_dir)

        # -------------------------------------------------------------------------
        # Запуск Telegram бота (в фоновой задаче)
        # -------------------------------------------------------------------------
        if config.telegram_enabled:
            from src.utils.telegram_bot import system_bot
            # Запуск бота без блокировки основного потока
            # Launching of the bot without blocking the main thread
            asyncio.create_task(system_bot.start())

        # -------------------------------------------------------------------------
        # Поиск и инициализация Foundry
        # -------------------------------------------------------------------------
        logger.info("Поиск Foundry...")
        foundry_base_url = resolve_foundry_base_url()

        if foundry_base_url and check_foundry(foundry_base_url):
            config.foundry_base_url = foundry_base_url
            logger.info(f'Foundry доступен: {foundry_base_url}')
        else:
            logger.info('Foundry недоступен — используйте hf:: / ollama:: / llama:: / lmstudio:: префиксы')

        # -------------------------------------------------------------------------
        # Параметры и запуск FastAPI
        # -------------------------------------------------------------------------
        host = config.api_host
        reload_enabled = config.api_reload
        log_level = config.api_log_level.lower()
        workers = config.api_workers

        if reload_enabled: # Проверка режима перезагрузки: в нем может быть только 1 воркер
            workers = 1

        port = get_server_port()

        logger.info('\nЗапуск сервера FastAPI')
        logger.info(f'   Хост: {host}')
        logger.info(f'   Порт: {port}')
        logger.info(f'   Перезагрузка: {reload_enabled}')
        logger.info(f'   Процессы (Workers): {workers}')
        logger.info('-' * 50)
        logger.info(f'Интерфейс: http://localhost:{port}')
        logger.info(f'Документация: http://localhost:{port}/docs')
        logger.info(f'Проверка: http://localhost:{port}/api/v1/health')
        logger.info('-' * 50)

        # Запуск uvicorn с полным контролем ошибок
        try:
            uvicorn.run(
                'src.api.main:app',
                host=host,
                port=port,
                reload=reload_enabled,
                workers=workers,
                log_level=log_level,
                timeout_keep_alive=300,
                timeout_graceful_shutdown=10,
            )
            return True
        except KeyboardInterrupt:
            logger.info('\nСервер остановлен пользователем')
            return True
        except ImportError as e:
            logger.error(f'Ошибка импорта - отсутствуют зависимости: {e}')
            logger.error('Попробуйте: venv\\Scripts\\python.exe -m pip install -r requirements.txt')
            return False
        except Exception as exc:
            logger.error(f'Ошибка запуска сервера: {exc}')
            logger.error('Проверьте, не занят ли порт и установлены ли все зависимости')
            return False
            
    except Exception as e:
        logger.error(f'Критическая ошибка в функции main: {e}')
        return False


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
