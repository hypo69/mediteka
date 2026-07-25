Настройка ngrok для локальной разработки
=========================================

Этот документ описывает настройку ngrok для доступа к локальному серверу из интернета.

Что такое ngrok?
--------------

ngrok - это инструмент, который создает защищенный туннель от публичного URL к вашему локальному серверу.
Это позволяет:
- Тестировать веб-приложения на реальных устройствах
- Интегрировать с внешними API (например, Telegram Bot Webhook)
- Демонстрировать приложение клиентам без деплоя
- Тестировать OAuth flows с правильными redirect URIs

Установка ngrok
-------------

### Windows (сChocolatey)
```bash
choco install ngrok
```

### Windows (скачивание)
1. Перейдите на [ngrok Downloads](https://ngrok.com/download)
2. Скачайте архив для Windows
3. Распакуйте в удобное место (например, `C:\Program Files\ngrok`)
4. Добавьте в PATH или используйте полный путь

### macOS (с Homebrew)
```bash
brew install ngrok
```

### Linux (APT)
```bash
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo gpg --dearmor -o /usr/share/keyrings/ngrok.gpg
echo "deb [signed-by=/usr/share/keyrings/ngrok.gpg] https://ngrok-agent.s3.amazonaws.com/deb main main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update
sudo apt install ngrok
```

### Linux (Snap)
```bash
sudo snap install ngrok
```

Настройка ngrok
--------------

### 1. Создайте аккаунт ngrok

1. Перейдите на [ngrok.com](https://ngrok.com/)
2. Зарегистрируйте аккаунт (бесплатный тариф достаточно для разработки)
3. Получите authtoken из [Auth Token page](https://dashboard.ngrok.com/get-started/your-authtoken)

### 2. Настройте authtoken

```bash
# Windows (PowerShell)
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN

# Linux/macOS
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN
```

Или создайте файл конфигурации `~/.ngrok2/ngrok.yml`:
```yaml
authtoken: YOUR_NGROK_AUTHTOKEN
```

Использование ngrok
------------------

### Базовое использование

Запустите туннель к вашему локальному серверу:

```bash
# Для сервера на порту 3000
ngrok http 3000
```

Вы увидите что-то вроде:
```
ngrok                                                 (Ctrl+C to quit)

Session Status                online
Account                       Your Name ( Plan: Free )
Version                       3.x.x
Region                        United States (us)
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.dev -> http://localhost:3000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

### Использование с проектом

1. Запустите ngrok:
   ```bash
   cd C:\mediateka
   ngrok http 3000
   ```

2. Скопируйте HTTPS URL (например: `https://abc123.ngrok-free.dev`)

3. Обновите `.env`:
   ```env
   GOOGLE_REDIRECT_URI=https://abc123.ngrok-free.dev/auth/google/callback
   ```

4. Добавьте URL в Google Cloud Console:
   - **Authorized redirect URIs:** `https://abc123.ngrok-free.dev/auth/google/callback`
   - **Authorized JavaScript origins:** `https://abc123.ngrok-free.dev`

5. Запустите приложение:
   ```bash
   python main.py
   ```

6. Откройте ngrok Web Interface (`http://127.0.0.1:4040`) для просмотра запросов

### Использование с Telegram Bot

Если вы используете Telegram Bot Webhook, обновите его:

```python
import requests

BOT_TOKEN = "7859139082:AAF_YjoCsnIN0zvoxOGPHDEnxfCvvMxshtg"
NGROK_URL = "https://abc123.ngrok-free.dev"

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    data={"url": f"{NGROK_URL}/tgwebhook"}
)

print(response.json())
```

### Сохранение статического URL (paid feature)

Free тариф выдает случайный URL каждый раз. Для статического URL:

1. Купите тариф Pro ($5/месяц)
2. В настройках домена выберите "Reserve a domain"
3. Запустите с вашим доменом:
   ```bash
   ngrok http https://your-reserved-domain.ngrok-free.dev 3000
   ```

Проблемы и Решения
-----------------

### "Error checking server: dial tcp 127.0.0.1:3000: connect: connection refused"

Приложение не запущено или слушает на другом порту. Проверьте:
- Запущено ли приложение: `python main.py`
- Правильный ли порт: `ngrok http 3000` (если сервер на 3000)

### "Invalid Host Header"

Если используете FastAPI с CORS, убедитесь, что разрешены ngrok домены:

```python
# В main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Для разработки
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
```

### "403 Forbidden" или "CORS Missing Allow Origin"

Добавьте ngrok URL вAUTHORIZED origins:
- **Google Cloud Console:** Authorized JavaScript origins
- **CORS middleware:** allow_origins

### "Tunnel abc123 not found"

ngrok сбросил сессию. Перезапустите ngrok и обновите credentials.

### "Rate limit exceeded"

Free тариф имеет ограничения. Попробуйте:
- Подождать несколько минут
- Обновить ngrok
- Рассмотреть upgrading до Pro

Альтернативы ngrok
------------------

- **Cloudflare Tunnel:** `cloudflared tunnel --url http://localhost:3000`
- **localtunnel:** `npx localtunnel --port 3000`
- **Serveo:** `ssh -R 80:localhost:3000 serveo.net`

Безопасность
-----------

- **Не коммитьте** ngrok authtoken в git
- Используйте `.gitignore`:
  ```gitignore
  .ngrok2/
  ngrok.yml
  ```
- В production используйте HTTPS
- Ограничьте доступ к ngrok Web Interface

Лицензия
--------

Этот проект распространяется под MIT.

Автор
-----

hypo69