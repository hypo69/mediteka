# Telegram Слушатель — администрирование

Listener Bot — пассивный Telegram бот. Слушает входящие сообщения, пишет в лог, не отвечает.

## Переменные окружения

| Переменная | Описание |
|---|---|
| `TELEGRAM_LISTENER_TOKEN` | Токен бота от @BotFather. Если не задан — бот не запускается. |

Добавьте в `.env`:

```env
TELEGRAM_LISTENER_TOKEN=123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Файл лога

Все входящие сообщения пишутся в:

```
~/.aiassistant/dialogs/listener_log.jsonl
```

Директория создаётся автоматически при первом запуске.

!!! warning "Размер файла"
    Файл растёт неограниченно. Настройте ротацию через `dialogs.max_size_mb` в `config.json` или периодически архивируйте вручную.

## Мониторинг

Проверить, что бот запущен:

```powershell
# В логах сервера при старте должна быть строка:
# INFO: ✅ Listener bot started.

# Если токен не задан:
# INFO: Listener bot disabled (TELEGRAM_LISTENER_TOKEN not set).
```

## Добавление бота в группу или канал

1. Откройте настройки группы/канала
2. Добавить участника → найдите бота по username
3. Для канала назначьте роль **администратор** (иначе бот не получает сообщения)

!!! info "Приватность бота"
    По умолчанию боты в группах получают только сообщения, начинающиеся с `/`.  
    Чтобы получать все сообщения — отключите **Group Privacy** через @BotFather:  
    `/mybots` → выберите бота → **Bot Settings** → **Group Privacy** → **Turn off**

## Ротация и очистка лога

```powershell
# Архивировать текущий лог
Move-Item ~/.aiassistant/dialogs/listener_log.jsonl `
          ~/.aiassistant/dialogs/listener_log_$(Get-Date -Format 'yyyyMMdd').jsonl

# Или очистить
Clear-Content ~/.aiassistant/dialogs/listener_log.jsonl
```

## Параметры config.json

| Параметр | По умолчанию | Описание |
|---|---|---|
| `dialogs.dir` | `~/.aiassistant/dialogs` | Директория для файлов диалогов |
| `dialogs.max_size_mb` | `100` | Максимальный размер директории (МБ) |
| `dialogs.retention_days` | `30` | Срок хранения файлов (дней) |
