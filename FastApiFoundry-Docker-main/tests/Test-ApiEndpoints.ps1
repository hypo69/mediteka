<#
.SYNOPSIS
    Проверка доступности и задержки REST API через PowerShell с поддержкой авторизации.
#>

$BaseUrl = "http://localhost:9696/api/v1"
$ApiKey = if ($env:API_KEY) { $env:API_KEY } else { "your_default_test_key" }

function Test-AiEndpoint {
    param (
        [string]$Name,
        [string]$Path,
        [object]$Payload
    )

    $Url = "$BaseUrl$Path"
    $Headers = @{ "X-API-Key" = $ApiKey }
    Write-Host "--- Тестирование: $Name ---" -ForegroundColor Cyan

    try {
        $Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $Response = Invoke-RestMethod -Uri $Url -Method Post -Body ($Payload | ConvertTo-Json) -ContentType "application/json" -Headers $Headers -TimeoutSec 15
        $Stopwatch.Stop()

        Write-Host "✅ Статус: 200 OK" -ForegroundColor Green
        Write-Host "⏱️  Задержка: $($Stopwatch.Elapsed.TotalMilliseconds.ToString('F2')) ms" -ForegroundColor Yellow
        
        # Вывод краткого превью JSON
        $JsonPreview = $Response | ConvertTo-Json -Depth 2
        if ($JsonPreview.Length -gt 150) { $JsonPreview = $JsonPreview.Substring(0, 150) + "..." }
        Write-Host "📝 Ответ: $JsonPreview" -ForegroundColor Gray
        return $true
    }
    catch {
        Write-Host "❌ Ошибка при обращении к $Url" -ForegroundColor Red
        Write-Host "⚠️  Сообщение: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

$Tests = @(
    @{
        Name    = "Генерация (Generate)"
        Path    = "/generate"
        Payload = @{ prompt = "PS Ping"; model = "foundry::qwen3-0.6b"; max_tokens = 5 }
    },
    @{
        Name    = "Чат (Chat)"
        Path    = "/chat"
        Payload = @{ message = "PS Chat Ping" }
    },
    @{
        Name    = "RAG Поиск (Search)"
        Path    = "/rag/search"
        Payload = @{ query = "deployment instructions"; top_k = 1 }
    }
)

Write-Host "🚀 Запуск PowerShell тестов API (Авторизация активна)`n" -ForegroundColor Magenta
$GlobalResults = foreach ($Test in $Tests) {
    Test-AiEndpoint -Name $Test.Name -Path $Test.Path -Payload $Test.Payload
    Write-Host ("-" * 40)
}

if ($GlobalResults -notcontains $false) { Write-Host "`n🎯 Все эндпоинты доступны." -ForegroundColor Green } else { Write-Host "`n⚠️ Обнаружены ошибки!" -ForegroundColor Red; exit 1 }