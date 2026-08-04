# Chat

**Файл:** `sdk/microsoft_foundry_sdk/chat.py`  
**Тип:** `.py`

---

### `FoundryChat` — Класс

```python
class FoundryChat
```

OpenAI-compatible chat interface for Foundry Local models.

Wraps the client returned by model.get_chat_client().
Maintains conversation history for multi-turn sessions.

Example:
    >>> from sdk.microsoft_foundry_sdk import FoundryManager, FoundryChat
    >>> mgr = FoundryManager()
    >>> mgr.initialize()
    >>> mgr.load_model("phi-4")
    >>> client = mgr.get_chat_client("phi-4")
    >>> chat = FoundryChat(client, model_id="phi-4")
    >>> response = chat.send("What is Python?")
    >>> print(response["content"])

### `__init__` — Функция

```python
def __init__(self, client: Any, model_id: str, system_prompt: str='You are a helpful AI assistant.', temperature: float=0.7, max_tokens: int=2048) -> None
```

### `send` — Функция

```python
def send(self, message: str) -> Dict[str, Any]
```

Send a message and get a response. Maintains history.

Args:
    message: User message text.

Returns:
    dict: success, content, model, usage.

### `stream` — Функция

```python
def stream(self, message: str) -> Generator[str, None, None]
```

Stream a response token by token.

Args:
    message: User message text.

Yields:
    str: Text chunks as they arrive.

### `clear_history` — Функция

```python
def clear_history(self) -> None
```

Clear conversation history.

### `history` — Функция

```python
@property
```

Return current conversation history (without system prompt).


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
