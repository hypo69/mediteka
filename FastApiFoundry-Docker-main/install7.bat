@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

set "PS_URL=https://github.com/PowerShell/PowerShell/releases/download/v7.4.6/PowerShell-7.4.6-win-x64.msi"
set "PS_URL_PAGE=https://aka.ms/powershell"
set "PS_MSI=%TEMP%\PowerShell-7-win-x64.msi"

echo.
echo ============================================================
echo  FastAPI Foundry - Installer (PowerShell 7 bootstrap)
echo ============================================================
echo.

:: --- 1. Check PowerShell 7+ ---
echo [check] Looking for PowerShell 7+...

set "PWSH="

for %%P in (pwsh.exe) do (
    if not defined PWSH set "PWSH=%%~$PATH:P"
)

if not defined PWSH (
    if exist "%ProgramFiles%\PowerShell\7\pwsh.exe" (
        set "PWSH=%ProgramFiles%\PowerShell\7\pwsh.exe"
    )
)

if not defined PWSH (
    if exist "%ProgramFiles%\PowerShell\7-preview\pwsh.exe" (
        set "PWSH=%ProgramFiles%\PowerShell\7-preview\pwsh.exe"
    )
)

if defined PWSH (
    for /f "tokens=*" %%V in ('"%PWSH%" -NoProfile -Command "$PSVersionTable.PSVersion.Major" 2^>nul') do set "PS_MAJOR=%%V"
    if !PS_MAJOR! GEQ 7 (
        echo [check] PowerShell !PS_MAJOR! found: %PWSH%
        goto :run_installer
    )
    echo [warn] Found pwsh.exe but version !PS_MAJOR! is too old.
    set "PWSH="
)

:: --- 2. PS7 not found - ask user ---
echo.
echo  PowerShell 7+ is required but not found on this system.
echo.
echo  Download page : %PS_URL_PAGE%
echo  Direct MSI    : %PS_URL%
echo.
echo  Options:
echo    [1] Install automatically (winget or download MSI)
echo    [2] Open download page in browser, install manually, then re-run
echo    [3] Exit
echo.
set /p "CHOICE=  Your choice (1/2/3): "

if "%CHOICE%"=="2" (
    start "" "%PS_URL_PAGE%"
    echo.
    echo  Browser opened. Install PowerShell 7, then run install7.bat again.
    echo.
    pause
    exit /b 0
)
if "%CHOICE%"=="3" exit /b 0
if not "%CHOICE%"=="1" (
    echo  Invalid choice. Exiting.
    pause
    exit /b 1
)

:: --- 3. Try winget ---
echo.
echo [try 1/3] winget...
winget --version >nul 2>&1
if not errorlevel 1 (
    winget install Microsoft.PowerShell --accept-source-agreements --accept-package-agreements --silent
    if not errorlevel 1 goto :find_pwsh_after_install
    echo [warn] winget install failed.
) else (
    echo [warn] winget not available.
)

:: --- 4. Try curl ---
echo [try 2/3] curl...
curl --version >nul 2>&1
if not errorlevel 1 (
    curl -L --progress-bar -o "%PS_MSI%" "%PS_URL%"
    if not errorlevel 1 goto :run_msi
    echo [warn] curl download failed.
) else (
    echo [warn] curl not available.
)

:: --- 5. Try PowerShell 5 Invoke-WebRequest ---
echo [try 3/3] PowerShell 5 Invoke-WebRequest...
set "PS5_CMD=[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri '%PS_URL%' -OutFile '%PS_MSI%' -UseBasicParsing; exit 0 } catch { Write-Host $_.Exception.Message; exit 1 }"
powershell -NoProfile -Command "%PS5_CMD%"
if not errorlevel 1 goto :run_msi

:: --- 6. All methods failed ---
echo.
echo [ERROR] Could not download PowerShell 7 automatically.
echo.
echo  Please download and install it manually:
echo    %PS_URL_PAGE%
echo.
echo  Then re-run install7.bat.
echo.
pause
exit /b 1

:run_msi
echo [install] Running MSI installer (silent)...
msiexec /i "%PS_MSI%" /quiet /norestart ADD_EXPLORER_CONTEXT_MENU_OPENPOWERSHELL=1 ENABLE_PSREMOTING=0
if errorlevel 1 (
    echo [ERROR] MSI installation failed.
    echo  Install manually: %PS_URL_PAGE%
    pause
    exit /b 1
)
del /f /q "%PS_MSI%" >nul 2>&1

:find_pwsh_after_install
set "PWSH=%ProgramFiles%\PowerShell\7\pwsh.exe"
if not exist "%PWSH%" (
    echo.
    echo [ERROR] pwsh.exe not found after install at: %PWSH%
    echo  Please restart cmd and run install7.bat again.
    pause
    exit /b 1
)
echo [ok] PowerShell 7 installed: %PWSH%

:: --- 7. Launch install.ps1 via pwsh ---
:run_installer
echo.
echo [run] Launching install.ps1 via PowerShell 7...
echo.

"%PWSH%" -ExecutionPolicy Bypass -File "%ROOT%\install.ps1" %*

:done
echo.
echo Done. Run start.ps1 to launch FastAPI Foundry.
echo.
pause
endlocal
