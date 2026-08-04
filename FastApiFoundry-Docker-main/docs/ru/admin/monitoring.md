# Мониторинг и логи

---

## Health check

```bash
GET http://localhost:9696/api/v1/health
```

Возвращает статус всех компонентов: FastAPI, Foundry, llama.cpp, RAG.

---

## Системная статистика

```bash
GET http://localhost:9696/api/v1/system/stats
```

RAM, CPU, загруженные модели.

---

## Логи

### Через веб-интерфейс

Вкладка **Logs** — просмотр в реальном времени с фильтрацией по уровню.

### Файлы логов

| Файл | Содержимое |
|---|---|
| `logs/fastapi-foundry.log` | Основной лог FastAPI |
| `logs/aiassistant-install.log` | Лог установки |
| `logs/autostart.log` | Лог автозапуска |

### Уровень логирования

```json
{
  "logging": {
    "level": "INFO"
  }
}
```

Уровни: `DEBUG`, `INFO`, `WARNING`, `ERROR`

---

## Диагностика

```powershell
# Проверить окружение
venv\Scripts\python.exe check_env.py

# Полная диагностика
venv\Scripts\python.exe diagnose.py

# Smoke-тесты всех endpoints
venv\Scripts\python.exe check_engine\smoke_all_endpoints.py
```

---

## Swagger UI

Интерактивная документация API с возможностью тестирования:

**http://localhost:9696/docs**
