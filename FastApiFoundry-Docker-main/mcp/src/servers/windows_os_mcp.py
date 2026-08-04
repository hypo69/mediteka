# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows OS MCP Server — typed tools for Windows system info
# =============================================================================
# Description:
#   MCP STDIO server exposing Windows OS diagnostics as structured tools.
#   Tools: get_processes, get_services, get_disk_info, get_network_stats,
#          get_system_info, kill_process, get_startup_items
#
# File: mcp/src/servers/windows_os_mcp.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial implementation for Windows OS agent
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import sys
import subprocess
import re
from pathlib import Path
from typing import Any, Dict, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _run_ps(script: str) -> str:
    """Run a PowerShell snippet and return stdout."""
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30
    )
    return result.stdout.strip() or result.stderr.strip()


def _safe_name(value: str, label: str = "name") -> str:
    """Allow only simple Windows identifiers used in service and task names."""
    value = str(value or "").strip()
    if not value or not re.fullmatch(r"[\w .:\-\\{}()]+", value):
        raise ValueError(f"Invalid {label}")
    return value


def _clamp_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def _truncate(value: str, limit: int = 8000) -> str:
    value = _clean_text(value)
    if len(value) <= limit:
        return value
    return value[:limit] + f"\n... truncated {len(value) - limit} chars ..."


def _clean_text(value: Any) -> str:
    """Normalize text so JSON-RPC output never contains invalid surrogate chars."""
    value = "" if value is None else str(value)
    return value.encode("utf-8", errors="replace").decode("utf-8", errors="replace")


def _ensure_script_dir() -> Path:
    path = Path("logs/os_diagnostic/generated_scripts")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _reject_unsafe_script(script: str, language: str) -> None:
    """Block obvious mutating operations in model-generated diagnostic scripts."""
    blocked_common = [
        r"\brm\s",
        r"\bdel\s",
        r"\berase\s",
        r"\bformat\b",
        r"\bshutdown\b",
        r"\brestart-computer\b",
        r"\bstop-computer\b",
    ]
    blocked_ps = [
        r"\bRemove-Item\b",
        r"\bMove-Item\b",
        r"\bRename-Item\b",
        r"\bSet-Item\b",
        r"\bNew-Item\b",
        r"\bStop-Process\b",
        r"\bStop-Service\b",
        r"\bSet-Service\b",
        r"\bStart-Service\b",
        r"\bRestart-Service\b",
        r"\bSet-ExecutionPolicy\b",
        r"\bInvoke-Expression\b",
        r"\biex\b",
        r"\bInvoke-WebRequest\b",
        r"\bInvoke-RestMethod\b",
    ]
    blocked_py = [
        r"\bos\.remove\s*\(",
        r"\bos\.rmdir\s*\(",
        r"\bos\.unlink\s*\(",
        r"\bshutil\.rmtree\s*\(",
        r"\bshutil\.move\s*\(",
        r"\bsubprocess\.",
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"\bopen\s*\([^)]*,\s*['\"][wa+]",
        r"\brequests\.",
        r"\burllib\.",
    ]

    patterns = blocked_common + (blocked_ps if language == "powershell" else blocked_py)
    for pattern in patterns:
        if re.search(pattern, script, flags=re.IGNORECASE):
            raise ValueError(f"Unsafe diagnostic script pattern blocked: {pattern}")


# ── Tool implementations ──────────────────────────────────────────────────────

def get_processes(sort_by: str = "cpu", top: int = 20) -> str:
    """Return top processes sorted by CPU or memory."""
    sort_map = {"cpu": "CPU", "memory": "WorkingSet", "name": "Name"}
    prop = sort_map.get(sort_by, "CPU")
    script = (
        f"Get-Process | Sort-Object -{prop} -Descending | Select-Object -First {top} "
        "Name, Id, CPU, @{N='MemMB';E={[math]::Round($_.WorkingSet/1MB,1)}}, "
        "Responding, StartTime | ConvertTo-Json -Compress"
    )
    return _run_ps(script)


def get_services(filter_status: str = "all") -> str:
    """Return Windows services, optionally filtered by status."""
    where = "" if filter_status == "all" else f"| Where-Object Status -eq '{filter_status}'"
    script = (
        f"Get-Service {where} | Select-Object Name, DisplayName, Status, StartType "
        "| ConvertTo-Json -Compress"
    )
    return _run_ps(script)


def get_disk_info() -> str:
    """Return disk usage for all drives."""
    script = (
        "Get-PSDrive -PSProvider FileSystem | "
        "Select-Object Name, @{N='UsedGB';E={[math]::Round($_.Used/1GB,2)}}, "
        "@{N='FreeGB';E={[math]::Round($_.Free/1GB,2)}}, "
        "@{N='TotalGB';E={[math]::Round(($_.Used+$_.Free)/1GB,2)}} "
        "| ConvertTo-Json -Compress"
    )
    return _run_ps(script)


def get_network_stats() -> str:
    """Return active TCP connections and network adapter stats."""
    script = (
        "$conn = Get-NetTCPConnection -State Established | "
        "Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State | "
        "Select-Object -First 30; "
        "$adapters = Get-NetAdapter | Where-Object Status -eq 'Up' | "
        "Select-Object Name, InterfaceDescription, LinkSpeed; "
        "@{connections=$conn; adapters=$adapters} | ConvertTo-Json -Depth 4 -Compress"
    )
    return _run_ps(script)


def get_system_info() -> str:
    """Return OS version, uptime, CPU and RAM summary."""
    script = (
        "$os = Get-CimInstance Win32_OperatingSystem; "
        "$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1; "
        "@{"
        "  OS=$os.Caption; Version=$os.Version; "
        "  UptimeHours=[math]::Round((New-TimeSpan $os.LastBootUpTime).TotalHours,1); "
        "  TotalRAM_GB=[math]::Round($os.TotalVisibleMemorySize/1MB,1); "
        "  FreeRAM_GB=[math]::Round($os.FreePhysicalMemory/1MB,1); "
        "  CPU=$cpu.Name; Cores=$cpu.NumberOfCores; "
        "  LoadPercent=$cpu.LoadPercentage"
        "} | ConvertTo-Json -Compress"
    )
    return _run_ps(script)


def kill_process(pid: int) -> str:
    """Stop a process by PID."""
    script = f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue; 'done'"
    return _run_ps(script)


def get_startup_items() -> str:
    """Return programs configured to run at startup."""
    script = (
        "Get-CimInstance Win32_StartupCommand | "
        "Select-Object Name, Command, Location, User | ConvertTo-Json -Compress"
    )
    return _run_ps(script)


def get_event_logs(log_name: str = "System", level: str = "Error", newest: int = 20) -> str:
    """Return recent Windows event log records."""
    allowed_logs = {"System", "Application", "Security"}
    allowed_levels = {"Critical": 1, "Error": 2, "Warning": 3, "Information": 4}
    log_name = log_name if log_name in allowed_logs else "System"
    level_value = allowed_levels.get(level, 2)
    newest = _clamp_int(newest, 20, 1, 100)
    script = (
        f"Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; Level={level_value}}} "
        f"-MaxEvents {newest} -ErrorAction SilentlyContinue | "
        "Select-Object TimeCreated, Id, ProviderName, LevelDisplayName, Message | "
        "ConvertTo-Json -Depth 3 -Compress"
    )
    return _run_ps(script)


def get_installed_apps() -> str:
    """Return installed applications from common uninstall registry keys."""
    script = (
        "$paths = @("
        "'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
        "'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
        "'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'"
        "); "
        "Get-ItemProperty $paths -ErrorAction SilentlyContinue | "
        "Where-Object DisplayName | "
        "Select-Object DisplayName, DisplayVersion, Publisher, InstallDate | "
        "Sort-Object DisplayName | ConvertTo-Json -Compress"
    )
    return _run_ps(script)


def get_local_users() -> str:
    """Return local Windows users and basic account state."""
    script = (
        "Get-LocalUser | "
        "Select-Object Name, Enabled, LastLogon, PasswordRequired, PasswordLastSet | "
        "ConvertTo-Json -Compress"
    )
    return _run_ps(script)


def get_scheduled_tasks(task_state: str = "all") -> str:
    """Return scheduled tasks, optionally filtered by state."""
    allowed_states = {"Ready", "Running", "Disabled"}
    where = f"| Where-Object State -eq '{task_state}'" if task_state in allowed_states else ""
    script = (
        f"Get-ScheduledTask {where} | Select-Object -First 100 "
        "TaskName, TaskPath, State, Author | ConvertTo-Json -Compress"
    )
    return _run_ps(script)


def get_defender_status() -> str:
    """Return Microsoft Defender computer status."""
    script = (
        "Get-MpComputerStatus | Select-Object "
        "AMServiceEnabled, AntivirusEnabled, AntispywareEnabled, RealTimeProtectionEnabled, "
        "IoavProtectionEnabled, NISEnabled, AntivirusSignatureLastUpdated, "
        "QuickScanEndTime, FullScanEndTime | ConvertTo-Json -Compress"
    )
    return _run_ps(script)


def get_windows_update_status() -> str:
    """Return Windows Update service state and latest installed hotfixes."""
    script = (
        "$svc = Get-Service wuauserv | Select-Object Name, DisplayName, Status, StartType; "
        "$hotfix = Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10 "
        "HotFixID, Description, InstalledOn; "
        "@{windows_update_service=$svc; recent_hotfixes=$hotfix} | ConvertTo-Json -Depth 4 -Compress"
    )
    return _run_ps(script)


def control_service(name: str, action: str) -> str:
    """Start, stop or restart a Windows service."""
    service_name = _safe_name(name, "service name")
    if action not in {"start", "stop", "restart"}:
        raise ValueError("Invalid service action")
    verb = {"start": "Start-Service", "stop": "Stop-Service", "restart": "Restart-Service"}[action]
    script = (
        f"{verb} -Name '{service_name}' -ErrorAction Stop; "
        f"Get-Service -Name '{service_name}' | Select-Object Name, Status, StartType | ConvertTo-Json -Compress"
    )
    return _run_ps(script)


def cleanup_temp_files(path: str = "", dry_run: bool = True, older_than_days: int = 7) -> str:
    """Estimate or remove old files from a temp directory."""
    target = _safe_name(path, "path") if path else "$env:TEMP"
    older_than_days = _clamp_int(older_than_days, 7, 1, 365)
    remove = "$true" if bool(dry_run) is False else "$false"
    script = (
        f"$target = '{target}' -replace \"'\", ''; "
        "if ($target -eq '$env:TEMP') { $target = $env:TEMP }; "
        "if (-not (Test-Path -LiteralPath $target -PathType Container)) { throw 'Invalid temp path' }; "
        f"$cutoff = (Get-Date).AddDays(-{older_than_days}); "
        "$items = Get-ChildItem -LiteralPath $target -File -Recurse -ErrorAction SilentlyContinue | "
        "Where-Object LastWriteTime -lt $cutoff; "
        "$summary = @{path=$target; dry_run=(-not " + remove + "); "
        "file_count=($items | Measure-Object).Count; "
        "total_mb=[math]::Round(($items | Measure-Object Length -Sum).Sum / 1MB, 2)}; "
        "if (" + remove + ") { $items | Remove-Item -Force -ErrorAction SilentlyContinue }; "
        "$summary | ConvertTo-Json -Compress"
    )
    return _run_ps(script)


def invoke_os_diagnostic(output_dir: str = "", window_hours: int = 24, skip_events: bool = False, no_store: bool = False) -> str:
    """Run the production PowerShell diagnostic toolkit and return its JSON report."""
    script_path = Path("scripts/os_diagnostic/Invoke-OsDiagnostic.ps1")
    if not script_path.exists():
        return json.dumps({"error": f"Diagnostic toolkit not found: {script_path}"}, ensure_ascii=False)

    window_hours = _clamp_int(window_hours, 24, 1, 24 * 30)
    command = [
        "pwsh",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-WindowHours",
        str(window_hours),
    ]
    if output_dir:
        command.extend(["-OutputDir", _safe_name(output_dir, "output_dir")])
    if skip_events:
        command.append("-SkipEvents")
    if no_store:
        command.append("-NoStore")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            cwd=str(Path.cwd()),
        )
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if result.returncode != 0:
            return json.dumps({
                "error": "diagnostic toolkit failed",
                "returncode": result.returncode,
                "stderr": stderr[:2000],
                "stdout": stdout[:2000],
            }, ensure_ascii=False)
        return stdout or json.dumps({"error": "diagnostic toolkit returned empty output"}, ensure_ascii=False)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "diagnostic toolkit timeout"}, ensure_ascii=False)
    except FileNotFoundError:
        return json.dumps({"error": "pwsh not found. Install PowerShell 7+"}, ensure_ascii=False)


def run_powershell_check(script: str, timeout_seconds: int = 30, reason: str = "") -> str:
    """Run a model-generated PowerShell diagnostic script from a temporary file."""
    _reject_unsafe_script(script, "powershell")
    timeout_seconds = _clamp_int(timeout_seconds, 30, 1, 120)
    script_dir = _ensure_script_dir()
    script_path = script_dir / "generated_check.ps1"
    script_path.write_text(script, encoding="utf-8")
    try:
        result = subprocess.run(
            ["pwsh", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            cwd=str(Path.cwd()),
        )
        return json.dumps({
            "language": "powershell",
            "reason": _clean_text(reason),
            "script_path": str(script_path),
            "returncode": result.returncode,
            "stdout": _truncate(result.stdout),
            "stderr": _truncate(result.stderr, 4000),
        }, ensure_ascii=False)
    except subprocess.TimeoutExpired:
        return json.dumps({"language": "powershell", "error": "timeout", "timeout_seconds": timeout_seconds}, ensure_ascii=False)
    except FileNotFoundError:
        return json.dumps({"language": "powershell", "error": "pwsh not found. Install PowerShell 7+"}, ensure_ascii=False)


def run_python_check(script: str, timeout_seconds: int = 30, reason: str = "") -> str:
    """Run a model-generated Python diagnostic script from a temporary file."""
    _reject_unsafe_script(script, "python")
    timeout_seconds = _clamp_int(timeout_seconds, 30, 1, 120)
    script_dir = _ensure_script_dir()
    script_path = script_dir / "generated_check.py"
    script_path.write_text(script, encoding="utf-8")
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            cwd=str(Path.cwd()),
        )
        return json.dumps({
            "language": "python",
            "reason": _clean_text(reason),
            "script_path": str(script_path),
            "returncode": result.returncode,
            "stdout": _truncate(result.stdout),
            "stderr": _truncate(result.stderr, 4000),
        }, ensure_ascii=False)
    except subprocess.TimeoutExpired:
        return json.dumps({"language": "python", "error": "timeout", "timeout_seconds": timeout_seconds}, ensure_ascii=False)


# ── Tool registry ─────────────────────────────────────────────────────────────

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "get_processes",
        "description": "Список запущенных процессов Windows (топ N по CPU или памяти)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sort_by": {"type": "string", "enum": ["cpu", "memory", "name"], "default": "cpu"},
                "top": {"type": "integer", "default": 20, "minimum": 1, "maximum": 100}
            }
        }
    },
    {
        "name": "get_services",
        "description": "Список служб Windows с фильтром по статусу",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filter_status": {"type": "string", "enum": ["all", "Running", "Stopped"], "default": "all"}
            }
        }
    },
    {
        "name": "get_disk_info",
        "description": "Использование дискового пространства по всем дискам",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_network_stats",
        "description": "Активные TCP соединения и статус сетевых адаптеров",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_system_info",
        "description": "Общая информация о системе: ОС, CPU, RAM, uptime",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "kill_process",
        "description": "Завершить процесс по PID",
        "inputSchema": {
            "type": "object",
            "properties": {"pid": {"type": "integer", "description": "Process ID"}},
            "required": ["pid"]
        }
    },
    {
        "name": "get_startup_items",
        "description": "Программы в автозагрузке Windows",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_event_logs",
        "description": "Последние события Windows Event Log по журналу и уровню",
        "inputSchema": {
            "type": "object",
            "properties": {
                "log_name": {"type": "string", "enum": ["System", "Application", "Security"], "default": "System"},
                "level": {"type": "string", "enum": ["Critical", "Error", "Warning", "Information"], "default": "Error"},
                "newest": {"type": "integer", "default": 20, "minimum": 1, "maximum": 100}
            }
        }
    },
    {
        "name": "get_installed_apps",
        "description": "Список установленных приложений Windows из реестра",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_local_users",
        "description": "Локальные пользователи Windows и состояние учетных записей",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_scheduled_tasks",
        "description": "Планировщик заданий Windows с фильтром по состоянию",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_state": {"type": "string", "enum": ["all", "Ready", "Running", "Disabled"], "default": "all"}
            }
        }
    },
    {
        "name": "get_defender_status",
        "description": "Состояние Microsoft Defender и защиты в реальном времени",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_windows_update_status",
        "description": "Состояние Windows Update и последние установленные обновления",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "control_service",
        "description": "Запустить, остановить или перезапустить службу Windows по имени",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Service name, e.g. wuauserv"},
                "action": {"type": "string", "enum": ["start", "stop", "restart"]}
            },
            "required": ["name", "action"]
        }
    },
    {
        "name": "cleanup_temp_files",
        "description": "Оценить или удалить старые временные файлы. По умолчанию dry_run=true",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Папка очистки. Пусто = текущий TEMP"},
                "dry_run": {"type": "boolean", "default": True},
                "older_than_days": {"type": "integer", "default": 7, "minimum": 1, "maximum": 365}
            }
        }
    },
    {
        "name": "invoke_os_diagnostic",
        "description": "Запустить production PowerShell OS diagnostic toolkit: snapshot, time-series, rule engine, correlation, health score, JSON/HTML/RST reports",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output_dir": {"type": "string", "description": "Папка для отчетов. Пусто = logs/os_diagnostic"},
                "window_hours": {"type": "integer", "default": 24, "minimum": 1, "maximum": 720},
                "skip_events": {"type": "boolean", "default": False},
                "no_store": {"type": "boolean", "default": False}
            }
        }
    },
    {
        "name": "run_powershell_check",
        "description": "Выполнить временный PowerShell diagnostic-only скрипт, созданный моделью. Подходит для WMI/CIM, Event Log, служб, реестра, Windows-настроек",
        "inputSchema": {
            "type": "object",
            "properties": {
                "script": {"type": "string", "description": "PowerShell код только для диагностики и чтения данных"},
                "timeout_seconds": {"type": "integer", "default": 30, "minimum": 1, "maximum": 120},
                "reason": {"type": "string", "description": "Почему выбран PowerShell"}
            },
            "required": ["script"]
        }
    },
    {
        "name": "run_python_check",
        "description": "Выполнить временный Python diagnostic-only скрипт, созданный моделью. Подходит для анализа JSON/time-series, вычислений, агрегаций и отчетности",
        "inputSchema": {
            "type": "object",
            "properties": {
                "script": {"type": "string", "description": "Python код только для диагностики, чтения и анализа"},
                "timeout_seconds": {"type": "integer", "default": 30, "minimum": 1, "maximum": 120},
                "reason": {"type": "string", "description": "Почему выбран Python"}
            },
            "required": ["script"]
        }
    },
]

_DISPATCH = {
    "get_processes": lambda a: get_processes(a.get("sort_by", "cpu"), int(a.get("top", 20))),
    "get_services": lambda a: get_services(a.get("filter_status", "all")),
    "get_disk_info": lambda a: get_disk_info(),
    "get_network_stats": lambda a: get_network_stats(),
    "get_system_info": lambda a: get_system_info(),
    "kill_process": lambda a: kill_process(int(a["pid"])),
    "get_startup_items": lambda a: get_startup_items(),
    "get_event_logs": lambda a: get_event_logs(a.get("log_name", "System"), a.get("level", "Error"), a.get("newest", 20)),
    "get_installed_apps": lambda a: get_installed_apps(),
    "get_local_users": lambda a: get_local_users(),
    "get_scheduled_tasks": lambda a: get_scheduled_tasks(a.get("task_state", "all")),
    "get_defender_status": lambda a: get_defender_status(),
    "get_windows_update_status": lambda a: get_windows_update_status(),
    "control_service": lambda a: control_service(a["name"], a["action"]),
    "cleanup_temp_files": lambda a: cleanup_temp_files(a.get("path", ""), bool(a.get("dry_run", True)), a.get("older_than_days", 7)),
    "invoke_os_diagnostic": lambda a: invoke_os_diagnostic(a.get("output_dir", ""), a.get("window_hours", 24), bool(a.get("skip_events", False)), bool(a.get("no_store", False))),
    "run_powershell_check": lambda a: run_powershell_check(a["script"], a.get("timeout_seconds", 30), a.get("reason", "")),
    "run_python_check": lambda a: run_python_check(a["script"], a.get("timeout_seconds", 30), a.get("reason", "")),
}


# ── MCP STDIO server loop ─────────────────────────────────────────────────────

def _respond(id_: Any, result: Any = None, error: Any = None) -> None:
    resp: Dict[str, Any] = {"jsonrpc": "2.0", "id": id_}
    if error:
        resp["error"] = error
    else:
        resp["result"] = result
    sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _handle(req: Dict[str, Any]) -> None:
    id_ = req.get("id")
    method = req.get("method", "")
    params = req.get("params") or {}

    if method == "initialize":
        _respond(id_, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "windows-os", "version": "0.7.1"}
        })
    elif method == "tools/list":
        _respond(id_, {"tools": TOOLS})
    elif method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments") or {}
        fn = _DISPATCH.get(name)
        if not fn:
            _respond(id_, error={"code": -32601, "message": f"Unknown tool: {name}"})
            return
        try:
            output = fn(args)
            _respond(id_, {"content": [{"type": "text", "text": output}]})
        except Exception as e:
            _respond(id_, error={"code": -32603, "message": str(e)})
    else:
        _respond(id_, error={"code": -32601, "message": f"Unknown method: {method}"})


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            _handle(req)
        except json.JSONDecodeError as e:
            _respond(None, error={"code": -32700, "message": f"Parse error: {e}"})


if __name__ == "__main__":
    main()
