# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Агент выполнения команд (Orchestrator)
# =============================================================================
# Описание:
#   Оркестрация запуска внешних CLI утилит через PowerShell wrapper.
#   Обеспечивает асинхронное выполнение и сбор метрик.
#
# File: src/utils/command_agent.py
# Project: Ai Assistant
# Package: src.utils
# Version: 0.6.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import os
import time
from pathlib import Path
from typing import List, Dict, Any
from src.logger import logger

class CommandAgent:
    """Класс для управления запуском внешних процессов через PS-обертку."""

    _instance = None

    def __new__(cls):
        # Обоснование Singleton: сохранение состояния предохранителя (circuit breaker) между вызовами API.
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_agent()
        return cls._instance

    def _init_agent(self) -> None:
        """Инициализация путей и состояний предохранителя."""
        self.root: Path = Path(__file__).parent.parent.parent
        self.ps_wrapper: Path = self.root / "src" / "utils" / "Invoke-LoggedCommand.ps1"
        self.default_log: Path = self.root / "logs" / "command_exec.jsonl"
        
        # Состояния предохранителя (Circuit Breaker)
        # Circuit Breaker states per command
        self._failure_counts: Dict[str, int] = {}
        self._last_failure_time: Dict[str, float] = {}
        self.FAILURE_THRESHOLD: int = 3
        self.COOLDOWN_SECONDS: int = 60
        self._last_path: str = os.environ.get('PATH', '') # Запоминание начального состояния PATH

    def reset_circuit_breaker(self, command: str = None) -> None:
        """Сброс состояния предохранителя (Circuit Breaker).
        
        Args:
            command (str, optional): Имя команды. Если None — сброс всех счетчиков.
        """
        if command:
            self._failure_counts[command] = 0
            self._last_failure_time[command] = 0.0
            logger.info(f"Предохранитель для команды '{command}' сброшен вручную.")
        else:
            self._failure_counts.clear()
            self._last_failure_time.clear()
            logger.info("Все предохранители агента команд сброшены.")

    async def run(self, command: str, args: List[str] = None, timeout: int = 30) -> Dict[str, Any]:
        """Запуск команды через PowerShell logging wrapper.

        ПОЧЕМУ ИСПОЛЬЗУЕТСЯ CIRCUIT BREAKER:
          - Предотвращение повторных запусков заведомо сломанных команд.
          - Защита системы от перегрузки при цикличных сбоях.

        Args:
            command (str): Исполняемый файл (например, 'foundry').
            args (List[str]): Список аргументов.
            timeout (int): Таймаут в секундах.

        Returns:
            Dict[str, Any]: Код возврата и захваченные потоки.
        """
        cmd_args: List[str] = args or []
        current_time: float = time.time()

        # Автоматическая проверка и обновление PATH при ошибке "команда не найдена"
        # Automatic check and PATH refresh on "command not found" error
        if not await self.test_command_available(command):
            logger.info(f"Команда '{command}' не найдена в текущем окружении. Попытка обновления PATH...")
            self.refresh_path_from_registry()
            
            # Проверка доступности после обновления
            # Availability check after refresh
            if not await self.test_command_available(command):
                logger.error(f"Команда '{command}' всё ещё недоступна после обновления PATH.")
                return {
                    "exit_code": -1,
                    "error": f"Command '{command}' not found even after registry PATH refresh",
                    "timed_out": False
                }

        # Автоматический сброс при изменении PATH
        # Automatic reset on PATH change detection
        current_path = os.environ.get('PATH', '')
        if current_path != self._last_path:
            logger.info("Обнаружено изменение системного PATH. Сброс предохранителей.")
            self.reset_circuit_breaker()
            self._last_path = current_path

        # Проверка состояния предохранителя
        # Circuit breaker state verification
        if self._failure_counts.get(command, 0) >= self.FAILURE_THRESHOLD:
            if (current_time - self._last_failure_time.get(command, 0)) < self.COOLDOWN_SECONDS:
                err_msg = f"⛔ Команда '{command}' заблокирована предохранителем (Circuit Breaker). " \
                          f"Попыток: {self._failure_counts.get(command, 0)}."
                logger.warning(err_msg)
                
                # Автоматическое уведомление в Telegram при блокировке
                # Automatic Telegram notification on command block
                try:
                    from .telegram_bot import system_bot
                    asyncio.create_task(system_bot.send_message(
                        f"⚠️ *Circuit Breaker Alert*\n"
                        f"Команда `{command}` временно заблокирована из-за частых ошибок. "
                        f"Попыток: {self._failure_counts.get(command, 0)}."
                    ))
                except Exception:
                    pass

                return {
                    "exit_code": -1,
                    "error": "Circuit breaker is open",
                    "jsonl_output": [],
                    "timed_out": False
                }
            # Сброс счетчика по истечении кулдауна
            # Counter reset after cooldown expiration
            self._failure_counts[command] = 0

        # Очистка лог-файла перед каждым запуском для предотвращения смешивания данных
        # Clearing the log file before each run to prevent data mixing
        if self.default_log.exists():
            self.default_log.unlink(missing_ok=True)

        # Формирование аргументов для PowerShell
        # Join command arguments into a single string to avoid array parsing issues
        ps_args: List[str] = [
            "-ExecutionPolicy", "Bypass",
            "-File", str(self.ps_wrapper),
            "-Command", command,
            "-OutFile", str(self.default_log),
            "-TimeoutSec", str(timeout)
        ]
        # Добавление аргументов команды Foundry/CLI как единой строки
        # Adding command arguments as a single joined string
        if cmd_args:
            ps_args.append("-Arguments")
            ps_args.append(' '.join(cmd_args))

        logger.debug(f"Выполнение команды: {command} {' '.join(cmd_args)}")

        try:
            # Асинхронный запуск процесса PowerShell
            # Asynchronous launch of the PowerShell process
            proc = await asyncio.create_subprocess_exec(
                "powershell",
                *ps_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()

            return {
                "exit_code": proc.returncode,
                "stdout": stdout.decode(errors="ignore"),
                "stderr": stderr.decode(errors="ignore")
            }
        except Exception as e:
            logger.error(f"Критический сбой агента команд: {e}")
            return {"exit_code": -1, "error": str(e)}

    async def run_wsl(self, command: str, args: List[str] = None, timeout: int = 30) -> Dict[str, Any]:
        """Выполнение bash-команды через подсистему WSL.

        ПОЧЕМУ ЭТО ВАЖНО:
          - Обеспечение совместимости с Linux-утилитами.
          - Использование единого механизма Circuit Breaker для всех типов команд.

        Args:
            command (str): Bash команда или имя исполняемого файла.
            args (List[str]): Аргументы команды.
            timeout (int): Таймаут выполнения в секундах.

        Returns:
            Dict[str, Any]: Результат выполнения (exit_code, stdout, stderr).
        """
        """Выполнение bash-команды через подсистему WSL (Заглушка)."""
        logger.info(f"WSL выполнение команды '{command}' пропущено (функционал в разработке)")
        return {
            "exit_code": -1,
            "error": "WSL support is placeholder for future updates",
            "timed_out": False
        }

    async def parse_foundry_status(self) -> Dict[str, Any]:
        """Парсинг состояния Foundry через HTTP-запрос к его API.

        Returns:
            Dict[str, Any]: Структурированные данные о статусе, порте и PID.
        """
        import aiohttp
        from urllib.parse import urlparse
        status_info: Dict[str, Any] = {
            "status": "unknown",
            "pid": None,
            "port": None,
            "health_check": "unknown",
            "errors": []
        }

        candidate_ports: list[int] = []

        def add_port(value: Any) -> None:
            try:
                port = int(value)
            except (TypeError, ValueError):
                return
            if port > 0 and port not in candidate_ports:
                candidate_ports.append(port)

        def add_url_port(value: Any) -> None:
            if not value:
                return
            try:
                parsed = urlparse(str(value))
                if parsed.port:
                    add_port(parsed.port)
            except ValueError:
                status_info["errors"].append(f"Invalid Foundry URL: {value!r}")

        # 1. Сначала проверяем активные настройки процесса и config.json.
        raw_port = os.getenv('FOUNDRY_DYNAMIC_PORT')
        add_port(raw_port)
        add_url_port(os.getenv('FOUNDRY_BASE_URL'))
        try:
            from config_manager import config
            add_url_port(config.foundry_base_url)
            add_port(config.foundry_port)
        except Exception as e:
            logger.debug(f"Не удалось прочитать config Foundry: {e}")

        # 2. Затем fallback на исторические порты и текущий порт Foundry Local.
        for port in [63995, 52632, 62171, 50477, 58130, 49152, 52987]:
            add_port(port)

        for port in candidate_ports:
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
                    async with session.get(f'http://127.0.0.1:{port}/v1/models') as resp:
                        if resp.status == 200:
                            status_info["status"] = "running"
                            status_info["port"] = port
                            os.environ['FOUNDRY_DYNAMIC_PORT'] = str(port)
                            return status_info
            except Exception as e:
                status_info["errors"].append(f"{port}: {e}")

        # 3. Если не удалось определить порт, считаем, что Foundry остановлен
        status_info["status"] = "stopped"
        return status_info

    async def execute_command_lines(self, command: str, args: List[str] = None, timeout: int = 30) -> Dict[str, List[str]]:
        """Выполнение команды с возвратом вывода в виде списка строк.

        Args:
            command (str): Исполняемый файл.
            args (List[str]): Параметры запуска.
            timeout (int): Ограничение времени выполнения.

        Returns:
            Dict[str, List[str]]: Группированные списки stdout и stderr.
        """
        result: Dict[str, Any] = await self.run(command, args, timeout)
        jsonl: List[Dict[str, Any]] = result.get("jsonl_output", [])
        
        return {
            "stdout": [item['msg'] for item in jsonl if item.get('stream') == 'stdout'],
            "stderr": [item['msg'] for item in jsonl if item.get('stream') == 'stderr']
        }

    async def test_command_available(self, command: str) -> bool:
        """Проверка доступности команды в системном окружении.

        ПОЧЕМУ ВЫБРАНО ЭТО РЕШЕНИЕ:
          - Предотвращение исключений при попытке запуска отсутствующих утилит.
          - Использование 'Get-Command' обеспечивает поиск как EXE, так и встроенных функций PowerShell.
          - Прямой запуск через asyncio минимизирует накладные расходы по сравнению с оберткой логирования.

        Args:
            command (str): Название исполняемого файла или команды.

        Returns:
            bool: True если команда найдена в путях окружения.
        """
        success: bool = False
        ps_cmd: str = f"Get-Command {command} -ErrorAction SilentlyContinue"
        proc = None

        try:
            # Выполнение облегченного поиска через PowerShell без записи в лог-файл
            # Execution of a lightweight search via PowerShell without writing to log file
            proc = await asyncio.create_subprocess_exec(
                "powershell",
                "-NoProfile", "-NonInteractive", "-Command", ps_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            success = (proc.returncode == 0)
        except Exception as e:
            logger.debug(f"Ошибка при проверке доступности команды '{command}': {e}")
            success = False

        return success

