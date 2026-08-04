# -*- coding: utf-8 -*-
# =============================================================================
# Название: FastAPI клиент (Invoke-FastApiRequest)
# =============================================================================
# Описание:
#   Выполняются HTTP-запросы к FastAPI серверу с поддержкой JSON,
#   логирования и обработки ошибок.
# =============================================================================
#
# <#
# .SYNOPSIS
#     Универсальный клиент для выполнения запросов к FastAPI серверу.
# .DESCRIPTION
#     Скрипт используется для взаимодействия с FastAPI API через HTTP.
#     Поддерживаются методы GET, POST, PUT, DELETE и PATCH.
#     Реализована автоматическая сериализация тела запроса в JSON,
#     логирование операций и обработка ошибок.
#     Может использоваться как CLI-инструмент или как базовый слой для автоматизации.
# .PARAMETER BaseUrl
#     Базовый URL сервера (например, http://localhost:9696).
# .PARAMETER Endpoint
#     Относительный путь API endpoint.
# .PARAMETER Method
#     HTTP метод (GET, POST, PUT, DELETE, PATCH).
# .PARAMETER Body
#     Тело запроса (Hashtable / Object).
# .PARAMETER Depth
#     Глубина сериализации JSON.
# .EXAMPLE
#     .\Invoke-FastApiRequest.ps1 -Endpoint '/api/v1/health'
# .EXAMPLE
#     .\Invoke-FastApiRequest.ps1 -Method POST -Endpoint '/api/v1/generate' -Body @{ prompt = 'Hello' }
# .OUTPUTS
#     System.String (JSON)
# .NOTES
#     Требуется доступ к FastAPI серверу.
# #>
# =============================================================================

param (
    [string]$BaseUrl = 'http://localhost:9696',
    [string]$Endpoint = '/api/v1/health',
    [ValidateSet('GET','POST','PUT','DELETE','PATCH')]
    [string]$Method = 'GET',
    [object]$Body = $null,
    [int]$Depth = 10
)

# --- Инициализируется логирование ---
function Write-Log {
    <#
    .SYNOPSIS
    Выполняется запись сообщения в лог.
    #>
    param (
        [string]$Message,
        [string]$Level = 'INFO'
    )

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $entry = "$timestamp [$Level] $Message"

    Write-Host $entry
}

# --- Выполняется HTTP-запрос ---
function Invoke-FastApiRequestInternal {
    <#
    .SYNOPSIS
    Выполняется HTTP-запрос к FastAPI серверу.

    .PARAMETER Url
    Полный URL запроса.

    .PARAMETER Method
    HTTP метод.

    .PARAMETER Body
    Тело запроса.

    .OUTPUTS
    System.Object
    #>

    param (
        [string]$Url,
        [string]$Method,
        [object]$Body
    )

    try {
        Write-Log "$Method $Url"

        $params = @{
            Uri = $Url
            Method = $Method
            ErrorAction = 'Stop'
        }

        if ($null -ne $Body) {
            $json = $Body | ConvertTo-Json -Depth 10
            $params['Body'] = $json
            $params['ContentType'] = 'application/json'
        }

        $response = Invoke-RestMethod @params

        Write-Log 'Ответ получен успешно'

        ...
        return $response
    }
    catch {
        Write-Log "Ошибка HTTP: $_" 'ERROR'

        if ($_.Exception.Response) {
            try {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $errorBody = $reader.ReadToEnd()
                Write-Log "Ответ сервера: $errorBody" 'ERROR'
            }
            catch {}
        }

        return $null
    }
}

# --- Основной процесс ---
try {
    Write-Log 'Запускается FastAPI клиент'

    $url = "$BaseUrl$Endpoint"

    $result = Invoke-FastApiRequestInternal -Url $url -Method $Method -Body $Body

    if ($null -ne $result) {
        $result | ConvertTo-Json -Depth $Depth
    }
    else {
        Write-Log 'Ответ отсутствует' 'WARN'
    }

    Write-Log 'Завершено выполнение'
}
catch {
    Write-Log "Критическая ошибка: $_" 'FATAL'
}