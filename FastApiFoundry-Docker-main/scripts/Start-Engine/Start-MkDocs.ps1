param([string]$Root, [string]$VenvPath, [string]$Config)

$docsPidFile = Join-Path $env:TEMP 'aiassistant-docs.pid'

try {
    $parsedConfig = Get-Content (Join-Path $Root $Config) -Raw | ConvertFrom-Json
    $docsServerConfig = $parsedConfig.docs_server
} catch { $docsServerConfig = $null }

if ($docsServerConfig -and $docsServerConfig.enabled) {
    $docsPort = $docsServerConfig.port
    
    # Очистка порта
    $oldConn = Get-NetTCPConnection -LocalPort $docsPort -State Listen -ErrorAction SilentlyContinue
    if ($oldConn) { Stop-Process -Id $oldConn.OwningProcess -Force }

    $siteDir = Join-Path $Root 'site'
    if (Test-Path $siteDir) {
        Write-Host "📚 Запуск статического сервера документации на порту $docsPort..." -ForegroundColor Cyan
        $proc = Start-Process powershell.exe -ArgumentList @(
            '-Command', "cd '$siteDir'; & '$VenvPath' -m http.server $docsPort"
        ) -WindowStyle Minimized -PassThru
    } else {
        Write-Host "📦 Сборка и запуск MkDocs на порту $docsPort..." -ForegroundColor Yellow
        try {
            Push-Location $Root
            & $VenvPath -m mkdocs build --quiet
            Pop-Location
        } catch {}
        
        $proc = Start-Process powershell.exe -ArgumentList @(
            '-Command', "cd '$Root'; & '$VenvPath' -m mkdocs serve -a 0.0.0.0:$docsPort"
        ) -WindowStyle Minimized -PassThru
    }
    
    if ($proc) {
        $proc.Id | Out-File $docsPidFile -Encoding UTF8
        
        # Проверка здоровья (Health Check)
        for ($i = 1; $i -le 10; $i++) {
            Start-Sleep -Seconds 1
            try {
                $r = Invoke-WebRequest -Uri "http://localhost:$docsPort" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
                if ($r.StatusCode -eq 200) {
                    Write-Host "✅ Сервер документации готов (PID: $($proc.Id))" -ForegroundColor Green
                    return
                }
            } catch {}
        }
        Write-Warning "Сервер документации запущен, но не ответил на проверку здоровья за отведенное время."
    }
}