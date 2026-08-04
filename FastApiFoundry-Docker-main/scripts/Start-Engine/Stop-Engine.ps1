param([string]$Root)

$PidFiles = @(
    Join-Path $env:TEMP 'fastapi-foundry.pid',
    Join-Path $env:TEMP 'aiassistant-llama.pid',
    Join-Path $env:TEMP 'aiassistant-docs.pid',
    Join-Path $env:TEMP 'opencode-foundry.pid',
    Join-Path $Root 'scripts\Install\.installer.pid'
)

Write-Host "`n🛑 Остановка всех компонентов системы..." -ForegroundColor Yellow

foreach ($file in $PidFiles) {
    if (Test-Path $file) {
        $pid = Get-Content $file -Raw -ErrorAction SilentlyContinue
        if ($pid -match '^\d+$') {
            try {
                $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($proc) {
                    # Попытка мягкого завершения (SIGTERM-like)
                    $proc.CloseMainWindow() | Out-Null
                    Start-Sleep -Seconds 3
                    
                    if (-not $proc.HasExited) {
                        $proc.Kill()
                        Write-Host "  ✅ Принудительно остановлен PID: $pid (файл: $(Split-Path $file -Leaf))" -ForegroundColor Gray
                    } else {
                        Write-Host "  ✅ Мягко остановлен PID: $pid (файл: $(Split-Path $file -Leaf))" -ForegroundColor Gray
                    }
                }
            } catch {}
        }
        Remove-Item $file -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "✨ Все компоненты остановлены." -ForegroundColor Green