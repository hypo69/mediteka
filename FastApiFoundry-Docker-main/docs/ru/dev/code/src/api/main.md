# Main

**Файл:** `src/api/main.py`  
**Тип:** `.py`

---

### `websocket_endpoint` — Функция

```python
@app.websocket('/ws/{room}')
```

WebSocket endpoint with room-based routing.

Args:
    websocket (WebSocket): WebSocket connection object.
    room (str): Room name for subscription (foundry, rag, system).


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
