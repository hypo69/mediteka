# Computer Admin Agent

`ComputerAdminAgent` реализует автономную диагностику Windows-компьютера поверх `BaseAgent` и `windows_os_mcp.py`.

Файлы:

| Файл | Назначение |
|---|---|
| `src/agents/computer_admin_agent.py` | агент и список tool definitions |
| `src/api/endpoints/agent.py` | registry и auto-selection |
| `mcp/src/servers/windows_os_mcp.py` | typed MCP tools для Windows |
| `scripts/os_diagnostic/Invoke-OsDiagnostic.ps1` | PowerShell toolkit диагностики |
| `tests/agents/test_computer_admin_agent.py` | тесты tools/schema |
| `tests/agents/test_agent_selection.py` | тесты auto-selection |

## Цель

Агент строится как основа для self-explaining OS diagnostic engine:

```text
1. time-series layer
2. rule engine
4. correlation + health scoring
3. LLM reasoning loop
```

Порядок важен: модель сначала получает факты и историю, потом объясняет состояние системы.

## Agent Registry

Агент регистрируется в `src/api/endpoints/agent.py`:

```python
def _build_registry():
    return {
        "computer_admin": ComputerAdminAgent(foundry_client),
    }
```

`AgentRequest.agent` по умолчанию равен `auto`.

Функция `select_agent_name()` сейчас выбирает `computer_admin`, если клиент указал `agent="auto"` и агент доступен. Это минимальный первый шаг к модели маршрутизации. Когда появятся несколько специализированных агентов, сюда можно добавить LLM-router или embedding-router.

API response содержит:

| Поле | Описание |
|---|---|
| `agent` | агент, запрошенный клиентом |
| `selected_agent` | агент, реально выбранный router-логикой |

## Инструменты агента

`ComputerAdminAgent.tools` возвращает OpenAI-compatible function calling schema. Все реальные операции делегируются в `windows_os_mcp.py` через `_call_mcp()`.

Ключевые инструменты:

| Tool | Назначение |
|---|---|
| `invoke_os_diagnostic` | основной snapshot/time-series/rule/correlation/health report |
| `run_powershell_check` | временный diagnostic-only PowerShell скрипт модели |
| `run_python_check` | временный diagnostic-only Python скрипт модели |
| `get_event_logs` | Windows Event Log |
| `get_defender_status` | Microsoft Defender |
| `get_windows_update_status` | Windows Update |
| `cleanup_temp_files` | dry-run или очистка старых temp-файлов |

## Выбор PowerShell или Python

System prompt агента задает правило выбора языка:

| Выбор | Основание |
|---|---|
| PowerShell | WMI/CIM, реестр, Event Log, службы, Windows-настройки |
| Python | JSON/time-series анализ, агрегации, scoring, отчеты, проверка файлов |

Модель передает объяснение выбора в аргументе `reason`.

Пример tool-call для PowerShell:

```json
{
  "script": "Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version | ConvertTo-Json -Compress",
  "reason": "PowerShell выбран, потому что проверка использует CIM/WMI Windows",
  "timeout_seconds": 30
}
```

Пример tool-call для Python:

```json
{
  "script": "import json, pathlib\np=pathlib.Path('logs/os_diagnostic/os_diagnostic_report.json')\nprint(json.dumps({'exists': p.exists()}))",
  "reason": "Python выбран для анализа JSON отчета",
  "timeout_seconds": 30
}
```

## PowerShell Diagnostic Toolkit

`Invoke-OsDiagnostic.ps1` выполняет автономный сбор и анализ:

- `Get-SystemSnapshot`;
- `Read-TimeSeries` / `Write-TimeSeries`;
- `Invoke-RuleEngine`;
- `Invoke-CorrelationEngine`;
- `Get-HealthScore`;
- `ConvertTo-HtmlReport`;
- `ConvertTo-RstReport`.

Выходные артефакты:

| Артефакт | Описание |
|---|---|
| `os_timeseries.jsonl` | append-only история snapshot |
| `os_diagnostic_report.json` | полный отчет для LLM и API |
| `os_diagnostic_report.html` | HTML-отчет |
| `os_diagnostic_report.rst` | строгий RST-отчет |

## Safety Model

Скрипты модели выполняются как временные файлы в:

```text
logs/os_diagnostic/generated_scripts/
```

Перед запуском применяется `_reject_unsafe_script()`, который блокирует очевидные изменяющие операции:

- удаление, перемещение и переименование файлов;
- остановка процессов и служб;
- изменение execution policy;
- `eval/exec` в Python;
- сетевые загрузки;
- прямые destructive shell-команды.

Это не полноценный sandbox. Для production рекомендуется запускать FastAPI процесс под ограниченным Windows-пользователем.

## Тестирование

Минимальный набор:

```powershell
venv\Scripts\python.exe -m pytest tests\agents\test_computer_admin_agent.py tests\agents\test_agent_selection.py -q
```

Проверка MCP tools:

```powershell
$payload = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
$payload | venv\Scripts\python.exe mcp\src\servers\windows_os_mcp.py
```

Проверка toolkit:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\os_diagnostic\Invoke-OsDiagnostic.ps1 `
  -OutputDir .\logs\os_diagnostic_test `
  -WindowHours 24 `
  -SkipEvents `
  -NoStore
```

## Дальнейшее развитие

Следующие шаги:

- заменить простую `select_agent_name()` на LLM-router при появлении нескольких агентов;
- добавить отдельный `observer`, `analyst`, `executor`, `verifier`;
- хранить time-series не только в JSONL, но и в SQLite;
- передавать summary в RAG для долгой памяти;
- добавить closed-loop diagnose -> decide -> fix -> verify с обязательным подтверждением опасных действий.
