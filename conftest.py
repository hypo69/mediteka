"""
Конфигурация тестов для mediteka.
Предоставляет фикстуры и настройки для всех тестов.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

import pytest

# Добавляем корень проекта в path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Настройка переменных окружения для тестов
os.environ['TEST_MODE'] = 'true'
os.environ['USE_FOUNDRY'] = 'false'
os.environ['PRELOAD_SILERO'] = 'false'


@pytest.fixture(scope='session')
def event_loop():
    """Предоставляет event loop для асинхронных тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def test_data_dir():
    """Путь к тестовым данным."""
    return ROOT / 'tests' / 'data'


@pytest.fixture
def mock_ai_model():
    """Мок для AI модели."""
    mock = Mock()
    mock.chat = AsyncMock()
    mock.chat_stream = AsyncMock()
    mock.ask = AsyncMock()
    mock.ask_with_tools = AsyncMock()
    mock.describe_image = AsyncMock()
    mock.upload_file = AsyncMock()
    mock.clear_history = Mock()
    return mock


@pytest.fixture
def mock_db():
    """Мок для MediaDatabase."""
    mock = Mock()
    mock.export_all = Mock(return_value=[])
    mock.export_movies = Mock(return_value=[])
    mock.export_series = Mock(return_value=[])
    mock.find_by_title = Mock(return_value=None)
    mock.find_duplicates = Mock(return_value=[])
    mock.get_categories = Mock(return_value=[])
    mock.add_record = Mock(return_value=1)
    mock.update_record = Mock(return_value=True)
    mock.delete_record = Mock(return_value=True)
    return mock


@pytest.fixture
def mock_qbt_client():
    """Мок для QBittorrentClient."""
    mock = Mock()
    mock.torrents = Mock(return_value=[])
    mock.add_torrent_by_url = Mock(return_value=True)
    mock.add_torrent_by_file = Mock(return_value=True)
    mock.recheck = Mock(return_value=True)
    mock.set_location = Mock(return_value=True)
    return mock


@pytest.fixture
def temp_db_path(tmp_path):
    """Временный путь к базе данных для тестов."""
    return tmp_path / 'test_media.db'


@pytest.fixture
def sample_media_records():
    """Пример записи медиа для тестов."""
    return [
        {
            'id': 1,
            'title': 'Test Movie',
            'title_ru': 'Тестовый Фильм',
            'title_orig': 'Test Movie',
            'type': 'movie',
            'disk_name': 'DISK_1',
            'year': 2024,
            'path': 'E:/Movies/Test Movie.mkv',
            'main_category': 'Боевики',
            'imdb_rating': 8.5,
            'kinopoisk_rating': 8.7,
        },
        {
            'id': 2,
            'title': 'Test Series',
            'title_ru': 'Тестовый Сериал',
            'title_orig': 'Test Series',
            'type': 'series',
            'disk_name': 'DISK_1',
            'year': 2024,
            'path': 'E:/Series/Test Series/S01E01.mkv',
            'main_category': 'Драмы',
            'season': 1,
            'episode': 1,
        },
    ]


@pytest.fixture
def sample_torrents():
    """Пример торрентов для тестов."""
    return [
        {
            'hash': 'abc123',
            'name': 'Test Torrent',
            'state': 'Downloading',
            'progress': 0.45,
            'size': 1073741824,
            'save_path': 'E:/Downloads',
        },
    ]


@pytest.fixture(autouse=True)
def setup_env():
    """Настройка окружения для каждого теста."""
    with patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'test_token',
        'GOOGLE_CLIENT_ID': 'test_client_id',
        'GOOGLE_CLIENT_SECRET': 'test_secret',
        'JWT_SECRET': 'test_jwt_secret',
        'NGROK_AUTOTOKEN': 'test_ngrok',
        'TMDB_API_KEY': 'test_tmdb_key',
        'GEMINI_API_KEY_NAMES': 'test_key',
    }, clear=True):
        yield
