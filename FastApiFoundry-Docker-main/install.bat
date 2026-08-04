@echo off
chcp 65001 >nul
setlocal

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "POWERSHELL="

echo.
echo ============================================================
echo  FastAPI Foundry - Installer
echo ============================================================
echo.

where powershell.exe >nul 2>&1
if not errorlevel 1 set "POWERSHELL=powershell.exe"

if not defined POWERSHELL (
    if exist "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" (
        set "POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
    )
)

if not defined POWERSHELL (
    echo [warn] powershell.exe was not found.
    echo [run] Falling back to install7.bat...
    echo.
    call "%ROOT%\install7.bat" %*
    exit /b %ERRORLEVEL%
)

echo [run] Launching install.ps1 via system PowerShell...
echo.

"%POWERSHELL%" -ExecutionPolicy Bypass -File "%ROOT%\install.ps1" %*
set "INSTALL_EXIT=%ERRORLEVEL%"

echo.
if "%INSTALL_EXIT%"=="0" (
    echo Done. Run start.ps1 to launch FastAPI Foundry.
) else (
    echo Installer exited with code %INSTALL_EXIT%.
)
echo.
pause
exit /b %INSTALL_EXIT%
