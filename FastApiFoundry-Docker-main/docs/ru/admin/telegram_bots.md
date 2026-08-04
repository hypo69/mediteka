# Telegram боты

Система включает два Telegram бота. Оба настраиваются через `.env`.

---

## Admin Bot

Бот для администратора — управление системой через Telegram.

```env
TELEGRAM_ADMIN_TOKEN=ваш_токен
TELEGRAM_ADMIN_IDS=123456789,987654321
```

Возможности:
- Статус сервисов
- Загрузка/выгрузка моделей
- Просмотр логов
- Отправка файлов для индексации в RAG

---

## HelpDesk Bot

Бот для пользователей — задают вопросы, получают ответы от AI.

```env
TELEGRAM_HELPDESK_TOKEN=ваш_токен
```

Настройки в `config.json`:

```json
{
  "telegram_helpdesk": {
    "enabled": true,
    "default_model": "foundry::qwen3-0.6b",
    "use_rag": true
  }
}
```

---

## Получить токен бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям — получите токен вида `123456789:AAF...`

---

## Получить свой chat_id

```powershell
venv\Scripts\python.exe scripts\Get-TelegramChatId.ps1
```

Или через скрипт диагностики:

```powershell
.\scripts\Get-TelegramChatId.ps1 -Token ваш_токен
```

Подробнее: [Telegram боты — разработчику](../dev/telegram_bots.md)
