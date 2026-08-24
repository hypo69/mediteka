@echo off
setlocal EnableDelayedExpansion
chcp 65001 > nul

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║              MEDITEKA — УСТАНОВКА                             ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: Определяем PowerShell 7 (pwsh) или fallback на Windows PowerShell 5
set "PS_EXE="
where pwsh.exe >nul 2>&1
if not errorlevel 1 (
    set "PS_EXE=pwsh.exe"
) else (
    where powershell.exe >nul 2>&1
    if not errorlevel 1 (
        set "PS_EXE=powershell.exe"
    )
)

if "%PS_EXE%"=="" (
    echo [ERROR] PowerShell не найден. Установите PowerShell 7: https://aka.ms/pscore6
    pause
    exit /b 1
)

echo [INFO] Используется: %PS_EXE%
echo.

:: Разблокируем install.ps1 от Mark of the Web и сразу запускаем.
:: -ExecutionPolicy Bypass действует только для этого одного запуска процесса.
%PS_EXE% -NoProfile -ExecutionPolicy Bypass -Command ^
    "Unblock-File -LiteralPath '%~dp0install.ps1' -ErrorAction SilentlyContinue; & '%~dp0install.ps1'"

if errorlevel 1 (
    echo.
    echo ╔═══════════════════════════════════════════════════════════════╗
    echo ║  [ERROR] Установка завершилась с ошибкой.                     ║
    echo ║  Проверьте вывод выше.                                        ║
    echo ╚═══════════════════════════════════════════════════════════════╝
    pause
    exit /b 1
)

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║  [OK] Установка завершена успешно!                            ║
echo ║  Для запуска: ./run.ps1                                       ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.
pause
endlocal