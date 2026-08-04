<!--
===============================================================================
Название процесса: Вспомогательные утилиты FastAPI Foundry
===============================================================================
Описание:
    Набор утилит для управления, мониторинга и обслуживания FastAPI Foundry системы.
    Включают сканирование AI моделей, управление портами и генерацию SSL.

Примеры:
    Сканирование моделей:
    python utils/ai_model_scanner.py
    python utils/foundry_model_finder.py
    python utils/port_manager.py --find-free

File: utils/README.md
Project: FastApiFoundry (Docker)
Version: 0.6.0
Author: hypo69
Copyright: © 2026 hypo69
Copyright: © 2026 hypo69
Date: 9 декабря 2025
===============================================================================
-->

# 🛠️ Utils

**Вспомогательные утилиты и инструменты для FastAPI Foundry**

---

## 📋 Описание

Эта директория содержит набор утилит для управления, мониторинга и обслуживания FastAPI Foundry системы.

## 📁 Утилиты

| Файл | Описание | Использование |
|------|----------|---------------|
| **`ai_model_scanner.py`** | Сканирование AI моделей в системе | Поиск Foundry, Ollama, HuggingFace моделей |
| **`foundry_model_finder.py`** | Поиск и анализ Foundry моделей | Определение доступных моделей Foundry |
| **`port_manager.py`** | Управление портами и процессами | Поиск свободных портов, управление сервисами |
| **`generate-ssl.py`** | Генерация SSL сертификатов | Создание HTTPS сертификатов для безопасности |
| **`pc_component_processor.py`** | Обработка и фильтрация данных о компонентах ПК | Классификация сборок, фильтрация брендов, нормализация JSON |

## 🚀 Использование

### 🔍 Сканирование AI моделей
```bash
# Поиск всех AI моделей в системе
python utils/ai_model_scanner.py

# Результат:
# - Foundry модели
# - Ollama модели  
# - HuggingFace кэш
# - Другие AI фреймворки
```

### 🤖 Поиск Foundry моделей
```bash
# Анализ доступных Foundry моделей
python utils/foundry_model_finder.py

# Показывает:
# - Установленные модели
# - Размеры файлов
# - Статус загрузки
```

### 🌐 Управление портами
```bash
# Поиск свободного порта
python utils/port_manager.py --find-free

# Остановка процесса на порту
python utils/port_manager.py --kill-port 8000

# Проверка статуса портов
python utils/port_manager.py --check-ports 8000,9696,50477
```

### 🔒 Генерация SSL
```bash
# Создание самоподписанного сертификата
python utils/generate-ssl.py

# Создание с параметрами
python utils/generate-ssl.py --domain localhost --days 365
```

## 🎯 Основные функции

### 🔍 AI Model Scanner
- **Автоматический поиск** моделей во всех стандартных директориях
- **Поддержка фреймворков**: Foundry, Ollama, HuggingFace, PyTorch
- **Анализ размеров** и типов файлов моделей
- **Проверка установок** AI фреймворков

### 🤖 Foundry Model Finder  
- **Поиск Foundry моделей** в системе
- **Анализ конфигураций** моделей
- **Проверка доступности** для загрузки
- **Рекомендации** по оптимизации

### 🌐 Port Manager
- **Поиск свободных портов** в заданном диапазоне
- **Управление процессами** на портах
- **Мониторинг сетевых соединений**
- **Автоматическое разрешение конфликтов**

### 🔒 SSL Generator
- **Генерация самоподписанных сертификатов**
- **Поддержка различных доменов**
- **Настраиваемый срок действия**
- **Автоматическое создание ключей**

## ⚙️ Конфигурация

### Переменные окружения
```bash
# Пути поиска моделей
AI_MODELS_PATH=/path/to/models
FOUNDRY_MODELS_PATH=/path/to/foundry/models

# Настройки портов
DEFAULT_PORT_RANGE=8000-9000
FOUNDRY_PORT=50477

# SSL настройки
SSL_CERT_PATH=./certs/
SSL_KEY_SIZE=2048
```

### Параметры командной строки
```bash
# AI Model Scanner
python utils/ai_model_scanner.py --scan-path /custom/path --format json

# Port Manager  
python utils/port_manager.py --range 8000-9000 --protocol tcp

# SSL Generator
python utils/generate-ssl.py --output ./certs/ --country US --org "FastAPI Foundry"
```

## 🧪 Примеры использования

### Полное сканирование системы
```python
from utils.ai_model_scanner import scan_all_ai_models

# Сканирование всех AI моделей
results = scan_all_ai_models()
print(f"Найдено моделей: {sum(len(data['models']) for data in results.values())}")
```

### Управление портами
```python
from utils.port_manager import find_free_port, kill_process_on_port

# Найти свободный порт
port = find_free_port(start=8000, end=9000)
print(f"Свободный порт: {port}")

# Освободить порт
kill_process_on_port(8000)
```

### Генерация SSL
```python
from utils.generate_ssl import generate_self_signed_cert

# Создать сертификат
cert_path, key_path = generate_self_signed_cert(
    domain="localhost",
    days=365,
    output_dir="./certs/"
)
```

## 📊 Мониторинг

### Системная информация
- **Использование портов** и сетевых ресурсов
- **Статус AI сервисов** (Foundry, Ollama)
- **Доступность моделей** и их размеры
- **SSL сертификаты** и их срок действия

### Логирование
- Все утилиты логируют свою работу
- Поддержка различных уровней логирования
- Структурированные логи в JSON формате

## 🔗 Интеграция

### С основным приложением
```python
# В FastAPI приложении
from utils.port_manager import find_free_port
from utils.ai_model_scanner import check_ai_installations

# Автоматический поиск порта
if config.auto_port:
    port = find_free_port()
    
# Проверка AI установок
ai_status = check_ai_installations()
```

### С веб-интерфейсом
- Утилиты интегрированы в веб-консоль
- Доступны через API endpoints
- Результаты отображаются в реальном времени

## 📖 Документация

- **[Installation Guide](../docs/installation.md)** - Установка и настройка
- **[Configuration Guide](../docs/configuration.md)** - Конфигурация системы
- **[SSL Setup](../docs/ssl-setup.md)** - Настройка HTTPS

---

**📖 Документация:** [Главное README](../README.md) | [Installation](../docs/installation.md) | [Configuration](../docs/configuration.md)