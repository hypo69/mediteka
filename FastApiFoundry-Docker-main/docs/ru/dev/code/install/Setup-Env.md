# Setup-Env.ps1

Интерактивный мастер создания файла `.env`.

**Файл:** `install\Setup-Env.ps1`  
**Запуск:** `powershell -ExecutionPolicy Bypass -File .\install\Setup-Env.ps1`

---

## Назначение

1. Проверяет существование `.env` — запрашивает подтверждение перезаписи
2. Копирует `.env.example` как шаблон
3. Опционально генерирует `API_KEY` и `SECRET_KEY` автоматически
4. Интерактивно запрашивает: GitHub-данные, API-ключи, URL Foundry, имя окружения
5. Сохраняет все значения в `.env`
6. Запускает `check_env.py` для валидации результата

---

## Параметры

| Параметр | Тип | Описание |
|---|---|---|
| `-Force` | switch | Перезаписать существующий `.env` без запроса |
| `-GenerateKeys` | switch | Автоматически сгенерировать `API_KEY` и `SECRET_KEY` |

---

## Примеры

```powershell
# Интерактивная настройка
powershell -ExecutionPolicy Bypass -File .\install\Setup-Env.ps1

# Перезаписать без вопросов
powershell -ExecutionPolicy Bypass -File .\install\Setup-Env.ps1 -Force

# Автогенерация ключей
powershell -ExecutionPolicy Bypass -File .\install\Setup-Env.ps1 -GenerateKeys
```

---

## Функции

### Generate-SecureKey

Генерирует криптографически стойкую случайную строку через `RNGCryptoServiceProvider`.

**Параметры:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `$Length` | int | `32` | Длина в байтах (выходная строка длиннее из-за Base64) |

**Возвращает:** URL-безопасную Base64-строку без `+`, `/`, `=`.

```powershell
$key = Generate-SecureKey 32
# Пример: "mK9xPqR2vL8nT5wY3jH6cB1dF4gA7eN0"
```

---

## Переменные в .env

| Переменная | Описание |
|---|---|
| `FOUNDRY_BASE_URL` | URL Foundry (если не автоопределяется) |
| `HF_TOKEN` | Токен HuggingFace |
| `API_KEY` | Ключ API для безопасности |
| `SECRET_KEY` | Секретный ключ |
| `GITHUB_USER` | GitHub логин |
| `GITHUB_PAT` | GitHub Personal Access Token |
| `ENVIRONMENT` | `development` или `production` |

!!! danger "Никогда не коммитьте .env"
    Файл `.env` добавлен в `.gitignore`. Не удаляйте эту запись.

