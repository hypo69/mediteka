# Command Agent

**Файл:** `src/utils/command_agent.py`  
**Тип:** `.py`

---

### `CommandAgent` — Класс

```python
class CommandAgent
```

Класс для управления запуском внешних процессов через PS-обертку.

### `__new__` — Функция

```python
def __new__(cls)
```

### `_init_agent` — Функция

```python
def _init_agent(self) -> None
```

Инициализация путей и состояний предохранителя.

### `reset_circuit_breaker` — Функция

```python
def reset_circuit_breaker(self, command: str=None) -> None
```

Сброс состояния предохранителя (Circuit Breaker).

Args:
    command (str, optional): Имя команды. Если None — сброс всех счетчиков.

### `run` — Функция

```python
async def run(self, command: str, args: List[str]=None, timeout: int=30) -> Dict[str, Any]
```

Запуск команды через PowerShell logging wrapper.

ПОЧЕМУ ИСПОЛЬЗУЕТСЯ CIRCUIT BREAKER:
  - Предотвращение повторных запусков заведомо сломанных команд.
  - Защита системы от перегрузки при цикличных сбоях.

Args:
    command (str): Исполняемый файл (например, 'foundry').
    args (List[str]): Список аргументов.
    timeout (int): Таймаут в секундах.

Returns:
    Dict[str, Any]: Код возврата и захваченные потоки.

### `run_wsl` — Функция

```python
async def run_wsl(self, command: str, args: List[str]=None, timeout: int=30) -> Dict[str, Any]
```

Выполнение bash-команды через подсистему WSL.

ПОЧЕМУ ЭТО ВАЖНО:
  - Обеспечение совместимости с Linux-утилитами.
  - Использование единого механизма Circuit Breaker для всех типов команд.

Args:
    command (str): Bash команда или имя исполняемого файла.
    args (List[str]): Аргументы команды.
    timeout (int): Таймаут выполнения в секундах.

Returns:
    Dict[str, Any]: Результат выполнения (exit_code, stdout, stderr).

### `parse_foundry_status` — Функция

```python
async def parse_foundry_status(self) -> Dict[str, Any]
```

Парсинг состояния Foundry через HTTP-запрос к его API.

Returns:
    Dict[str, Any]: Структурированные данные о статусе, порте и PID.

### `execute_command_lines` — Функция

```python
async def execute_command_lines(self, command: str, args: List[str]=None, timeout: int=30) -> Dict[str, List[str]]
```

Выполнение команды с возвратом вывода в виде списка строк.

Args:
    command (str): Исполняемый файл.
    args (List[str]): Параметры запуска.
    timeout (int): Ограничение времени выполнения.

Returns:
    Dict[str, List[str]]: Группированные списки stdout и stderr.

### `test_command_available` — Функция

```python
async def test_command_available(self, command: str) -> bool
```

Проверка доступности команды в системном окружении.

ПОЧЕМУ ВЫБРАНО ЭТО РЕШЕНИЕ:
  - Предотвращение исключений при попытке запуска отсутствующих утилит.
  - Использование 'Get-Command' обеспечивает поиск как EXE, так и встроенных функций PowerShell.
  - Прямой запуск через asyncio минимизирует накладные расходы по сравнению с оберткой логирования.

Args:
    command (str): Название исполняемого файла или команды.

Returns:
    bool: True если команда найдена в путях окружения.

### `add_port` — Функция

```python
def add_port(value: Any) -> None
```

### `add_url_port` — Функция

```python
def add_url_port(value: Any) -> None
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
