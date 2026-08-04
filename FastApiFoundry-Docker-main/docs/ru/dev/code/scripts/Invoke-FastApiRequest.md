# Invoke Fastapirequest

**Файл:** `scripts/Invoke-FastApiRequest.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Название: FastAPI клиент (Invoke-FastApiRequest)
=============================================================================
Описание:
Выполняются HTTP-запросы к FastAPI серверу с поддержкой JSON,
логирования и обработки ошибок.
=============================================================================

<#
.SYNOPSIS
Универсальный клиент для выполнения запросов к FastAPI серверу.
.DESCRIPTION
Скрипт используется для взаимодействия с FastAPI API через HTTP.
Поддерживаются методы GET, POST, PUT, DELETE и PATCH.
Реализована автоматическая сериализация тела запроса в JSON,
логирование операций и обработка ошибок.
Может использоваться как CLI-инструмент или как базовый слой для автоматизации.
.PARAMETER BaseUrl
Базовый URL сервера (например, http://localhost:9696).
.PARAMETER Endpoint
Относительный путь API endpoint.
.PARAMETER Method
HTTP метод (GET, POST, PUT, DELETE, PATCH).
.PARAMETER Body
Тело запроса (Hashtable / Object).
.PARAMETER Depth
Глубина сериализации JSON.
.EXAMPLE
.\Invoke-FastApiRequest.ps1 -Endpoint '/api/v1/health'
.EXAMPLE
.\Invoke-FastApiRequest.ps1 -Method POST -Endpoint '/api/v1/generate' -Body @{ prompt = 'Hello' }
.OUTPUTS
System.String (JSON)
.NOTES
Требуется доступ к FastAPI серверу.
>
=============================================================================

### `Write-Log`

### `Invoke-FastApiRequestInternal`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
