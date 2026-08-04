# Провайдеры и модели

## Поддерживаемые провайдеры

| Провайдер | ID | Base URL | Формат ключа |
|---|---|---|---|
| Google Gemini | `gemini` | `generativelanguage.googleapis.com` | `AIza…` |
| OpenAI | `openai` | `api.openai.com/v1` | `sk-…` |
| OpenRouter | `openrouter` | `openrouter.ai/api/v1` | `sk-or-…` |
| Anthropic Claude | `anthropic` | `api.anthropic.com/v1` | `sk-ant-…` |
| Mistral AI | `mistral` | `api.mistral.ai/v1` | произвольный |
| Groq | `groq` | `api.groq.com/openai/v1` | `gsk_…` |
| Cohere | `cohere` | `api.cohere.com/v2` | произвольный |
| DeepSeek | `deepseek` | `api.deepseek.com` | `sk-…` |
| xAI Grok | `xai` | `api.x.ai/v1` | `xai-…` |
| NVIDIA NIM | `nvidia` | `integrate.api.nvidia.com/v1` | `nvapi-…` |
| Custom (OpenAI-compatible) | `custom` | задаётся вручную | произвольный |

## Настройка провайдера

### Добавление API-ключа

1. Открыть **⚙️ Providers & Models**
2. Найти нужного провайдера — карточка свёрнута если ключей нет
3. Ввести ключ в поле → нажать **+ Add key**
4. Ключ сохраняется в `chrome.storage.sync` немедленно

Можно добавить несколько ключей на одного провайдера (ротация, разные проекты).

### Загрузка моделей

После добавления ключа нажать **Load models** — расширение запросит список моделей через API провайдера и сохранит в `chrome.storage.local`.

Если нужной модели нет в списке — добавить вручную через поле **Add model ID manually**.

### Выбор активной пары ключ → модель

1. Нажать **Load models** под нужным ключом
2. Кликнуть на модель в списке — она автоматически сохраняется как активная
3. Или нажать **Set Active** для явного переключения

Активная пара отображается в popup расширения.

## Custom провайдер (FastAPI Foundry)

Провайдер `custom` позволяет подключиться к любому OpenAI-совместимому серверу.

### Подключение к FastAPI Foundry

```
Base URL: http://localhost:9696/v1
API key:  (пусто, если API_KEY не задан в .env)
```

После нажатия **Load models** расширение запросит `GET /v1/models` и покажет доступные модели.

### Подключение к Ollama

```
Base URL: http://localhost:11434/v1
API key:  (пусто)
```

### Подключение к LM Studio

```
Base URL: http://localhost:1234/v1
API key:  (пусто)
```

## Оверрайд провайдера для суммаризации

На вкладке **🤖 Summarizer** можно задать отдельный провайдер и модель специально для суммаризации — независимо от активного провайдера в чате.

Это полезно когда:
- для чата используется дорогая модель (GPT-4o), а для суммаризации — дешёвая (GPT-4o-mini)
- суммаризация идёт через локальный Foundry, а чат — через OpenAI

## Экспорт и импорт конфигурации

### Экспорт

Кнопка **💾 Export** на странице провайдеров сохраняет в JSON:
- все API-ключи всех провайдеров (в открытом виде)
- кастомные модели
- активный провайдер, модель, индекс ключа
- язык суммаризации
- кэш загруженных моделей

!!! warning "Безопасность"
    Файл экспорта содержит API-ключи в открытом виде. Не публикуйте его и не передавайте по незащищённым каналам.

### Импорт

Кнопка **📂 Import** полностью заменяет текущую конфигурацию данными из файла. Страница перезагружается после импорта.

## Реестр провайдеров — providers.js

Каждый провайдер описывается объектом:

```js
{
    label: 'Google Gemini',           // отображаемое название
    keyPlaceholder: 'AIza…',          // подсказка в поле ввода ключа
    keyHint: 'aistudio.google.com/…', // URL страницы получения ключа
    fetchModels: async (apiKey) => [  // функция загрузки моделей
        { id: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' }
    ]
}
```

### Добавление нового провайдера

1. Добавить объект в `providers.js`:

```js
myprovider: {
    label: 'My Provider',
    keyPlaceholder: 'mp-…',
    keyHint: 'myprovider.com/api-keys',
    fetchModels: async (apiKey) => {
        const r = await fetch('https://api.myprovider.com/v1/models', {
            headers: { Authorization: `Bearer ${apiKey}` }
        });
        const d = await r.json();
        if (!r.ok) throw new Error(d.error?.message || `HTTP ${r.status}`);
        return (d.data || []).map(m => ({ id: m.id, label: m.name || m.id }));
    }
}
```

2. Добавить URL в `manifest.json → host_permissions`:

```json
"https://api.myprovider.com/"
```

3. Если провайдер не OpenAI-совместимый — добавить коннектор в `connectors/` и маршрут в `summarizer.js` и `chat.js`.
