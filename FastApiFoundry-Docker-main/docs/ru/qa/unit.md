# Юнит-тесты

Файлы: `tests/unit/`

Изолированная проверка функций и классов без внешних зависимостей.

---

## test_json_utils.py

**Модуль:** `src/utils/json.py` → функция `j_loads`

Проверяет корректность парсинга JSON-строк во всех граничных случаях.

| Тест | Сценарий |
|---|---|
| `test_j_loads_valid` | Корректная JSON-строка с разными типами значений |
| `test_j_loads_empty` | Пустой объект `{}` |
| `test_j_loads_error` | Битый JSON — ожидается `json.JSONDecodeError` |
| `test_unicode_support` | Строка с кириллицей — проверка целостности UTF-8 |

**Пример теста:**

```python
def test_j_loads_error(self):
    """Validation of exception on malformed JSON."""
    with pytest.raises(json.JSONDecodeError):
        j_loads('{"status":')
```

**Запуск:**

```powershell
venv\Scripts\pytest.exe tests/unit/test_json_utils.py -v
```

---

## Добавление новых юнит-тестов

Шаблон для нового файла в `tests/unit/`:

```python
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: <Module> Unit Tests
# =============================================================================
# File: tests/unit/test_<module>.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# =============================================================================

import pytest
from src.<package>.<module> import <function>


class Test<Module>:
    """Unit tests for <description>."""

    def test_<scenario>(self):
        """<What is validated>."""
        result = <function>(<input>)
        assert result == <expected>
```

**Правила:**

- Импорт только из `src/` — никаких относительных импортов
- Внешние зависимости заменяются через `mocker.patch` или `MagicMock`
- Тест не должен обращаться к сети или файловой системе
