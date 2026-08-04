param([string]$Root)

. (Join-Path $Root 'scripts\Get-FoundryUtils.ps1')
Write-Host '🔍 Проверка Microsoft Foundry Local...' -ForegroundColor Cyan

$foundryPort = Get-FoundryPort
if ($foundryPort) {
    Write-Host "✅ Foundry уже запущен (Порт: $foundryPort)" -ForegroundColor Green
} else {
    if (-not (Test-FoundryCli)) {
        Write-Warning "Foundry CLI не найден. Возможности AI будут ограничены."
    } else {
        try {
            Start-Process -FilePath "foundry" -ArgumentList "service", "start" -WindowStyle Minimized
            for ($i = 1; $i -le 10; $i++) {
                Start-Sleep -Seconds 2
                $foundryPort = Get-FoundryPort
                if ($foundryPort) {
                    Write-Host "✅ Foundry успешно запущен на порту $foundryPort" -ForegroundColor Green
                    break
                }
                Write-Host "⏳ Ожидание Foundry... ($i/10)" -ForegroundColor Gray
            }
        } catch {
            Write-Error "Критическая ошибка при запуске Foundry: $_"
        }
    }
}

if ($foundryPort) {
    $env:FOUNDRY_DYNAMIC_PORT = $foundryPort
    $env:FOUNDRY_BASE_URL = "http://localhost:$foundryPort/v1/"
}