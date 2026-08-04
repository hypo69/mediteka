FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем только requirements.txt — ключ к кэшированию pip
COPY requirements.txt /app/requirements.txt

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копируем весь остальной код проекта
COPY src/ ./src/
COPY static/ ./static/
COPY docs/ ./docs/
COPY mcp-servers/ ./mcp-servers/
COPY run.py .
COPY rag_indexer.py .

# Создание директорий данных
RUN mkdir -p logs rag_index

# Создание непривилегированного пользователя
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Переменные окружения
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000
ENV FASTAPI_FOUNDRY_MODE=production

# Порт приложения
EXPOSE 8000

# Запуск приложения
CMD ["python", "run.py"]
