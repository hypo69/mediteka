# Websocket Manager

**Файл:** `src/api/websocket_manager.py`  
**Тип:** `.py`

---

### `ConnectionManager` — Класс

```python
class ConnectionManager
```

Класс для управления жизненным циклом WebSocket соединений и рассылки уведомлений.

### `__init__` — Функция

```python
def __init__(self) -> None
```

Инициализация хранилища соединений и комнат.

### `connect` — Функция

```python
async def connect(self, websocket: WebSocket, room: Optional[str]=None) -> None
```

Регистрация нового соединения.

Args:
    websocket (WebSocket): Объект веб-сокета.
    room (str, optional): Название комнаты для подписки.

### `disconnect` — Функция

```python
def disconnect(self, websocket: WebSocket, room: Optional[str]=None) -> None
```

Удаление закрытого соединения из реестра.

Args:
    websocket (WebSocket): Объект веб-сокета.
    room (str, optional): Название комнаты.

### `send_personal_message` — Функция

```python
async def send_personal_message(self, message: dict, websocket: WebSocket) -> None
```

Отправка приватного сообщения конкретному клиенту.

### `broadcast` — Функция

```python
async def broadcast(self, message: dict, room: Optional[str]=None) -> None
```

Рассылка уведомления группе клиентов или всем сразу.

Обоснование:
  - Поддержка комнат позволяет экономить трафик и ресурсы клиента.
  - Автоматическая очистка "мёртвых" соединений при попытке отправки.

Args:
    message (dict): Данные для отправки.
    room (str, optional): Название целевой комнаты. Если None — всем.

### `wait_for_permission` — Функция

```python
async def wait_for_permission(self, permission_id: str) -> bool
```

Регистрация ожидания подтверждения от пользователя.

### `handle_hitl_response` — Функция

```python
async def handle_hitl_response(self, permission_id: str, confirmed: bool) -> None
```

Обработка ответа пользователя и сохранение решения в Chat DB.

Args:
    permission_id (str): Идентификатор запроса.
    confirmed (bool): Выбор пользователя (разрешить/отклонить).


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
