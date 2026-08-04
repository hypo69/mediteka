# Быстрый старт для администратора

Этот раздел для тех, кто разворачивает систему с нуля.

---

## Минимальный путь к работающей системе

```powershell
# 1. Получить код
git clone https://github.com/hypo69/FastApiFoundry-Docker.git
cd FastApiFoundry-Docker

# 2. Установить зависимости
install.bat

# 3. Запустить
.\start.ps1
```

После запуска система доступна по адресу **http://localhost:9696**

---

## Что происходит при первом запуске

`install.bat` → `install.ps1`:

- Создаёт Python виртуальное окружение `venv/`
- Устанавливает зависимости из `requirements.txt`
- Создаёт `.env` из `.env.example`
- Опционально устанавливает: Foundry Local, LM Studio, Tesseract OCR, RAG-зависимости

`start.ps1`:

- Активирует venv
- Загружает переменные из `.env`
- Находит или запускает Foundry Local
- Запускает FastAPI сервер на порту 9696

---

## Минимальная конфигурация

После установки отредактируйте `.env`:

```env
# Токен HuggingFace (нужен для закрытых моделей: Gemma, Llama)
HF_TOKEN=hf_ваш_токен
```

Всё остальное работает с настройками по умолчанию.

---

## Проверка установки

```powershell
# Проверить окружение
venv\Scripts\python.exe check_env.py

# Health check
curl http://localhost:9696/api/v1/health
```

---

## Что дальше

- [Установка — подробно](installation.md) — все параметры install.ps1
- [Конфигурация](configuration.md) — config.json и .env
- [Запуск и остановка](run_stop.md) — start.ps1, stop.ps1, автозапуск
- [Бэкенды и модели](backends.md) — Foundry, llama.cpp, HuggingFace, Ollama
