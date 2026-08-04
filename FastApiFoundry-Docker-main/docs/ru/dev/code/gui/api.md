# Api

**Файл:** `gui/api.py`  
**Тип:** `.py`

---

### `Api` — Класс

```python
class Api
```

Класс взаимодействия между JS и Python через pywebview bridge.

### `run_powershell` — Функция

```python
def run_powershell(self, command: str) -> str
```

Выполнение PowerShell команды.

Args:
    command (str): Текст команды для выполнения.

Returns:
    str: Стандартный вывод (stdout) или текст ошибки.

ПОЧЕМУ -NoProfile:
  Ускорение запуска и предотвращение конфликтов с пользовательскими скриптами профиля.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
