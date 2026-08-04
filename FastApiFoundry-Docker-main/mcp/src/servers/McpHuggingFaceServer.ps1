# =====================================================================
# File: mcp-huggingface.ps1
# Description: Minimal Model Context Protocol (MCP) server for Hugging Face
# Author: hypo69
# Requirements:
#   - PowerShell 7.2+
#   - Internet access
#   - Hugging Face API token (set via environment variable HF_TOKEN)
# =====================================================================

param(
    [string]$Model = "meta-llama/Llama-3-8b-instruct",
    [int]$Port = 8080
)

# ======================
# Dependencies & Config
# ======================
$ErrorActionPreference = "Stop"
$HF_TOKEN = $env:HF_TOKEN
if (-not $HF_TOKEN) {
    Write-Host "❌ Environment variable HF_TOKEN not set. Run:"
    Write-Host "`$env:HF_TOKEN = 'hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx'"
    exit 1
}

$Prefix = "http://+:$Port/mcp/"
Write-Host "🚀 Starting MCP HuggingFace server on $Prefix"
Write-Host "🔗 Model: $Model"

# ======================
# Start HTTP Listener
# ======================
$Listener = [System.Net.HttpListener]::new()
$Listener.Prefixes.Add($Prefix)
$Listener.Start()
Write-Host "✅ Listening for incoming connections..."

# ======================
# Helper: Send SSE event
# ======================
function Send-SSEEvent {
    param(
        [System.IO.StreamWriter]$Writer,
        [string]$EventType,
        [string]$Data
    )
    $Writer.WriteLine("event: $EventType")
    $Writer.WriteLine("data: $Data")
    $Writer.WriteLine("")
    $Writer.Flush()
}

# ======================
# Main Loop
# ======================
while ($true) {
    $Context = $Listener.GetContext()
    $Request = $Context.Request
    $Response = $Context.Response
    $Writer = [System.IO.StreamWriter]::new($Response.OutputStream)

    Write-Host "📥 Connection from $($Request.RemoteEndPoint)"

    if ($Request.Url.AbsolutePath -ne "/mcp/") {
        $Response.StatusCode = 404
        $Writer.Write("Not Found")
        $Writer.Flush()
        $Response.Close()
        continue
    }

    $Response.ContentType = "text/event-stream"
    $Response.Headers.Add("Cache-Control", "no-cache")
    $Response.Headers.Add("Connection", "keep-alive")

    try {
        # Читаем prompt из параметров (например, ?prompt=hello)
        $Prompt = $Request.QueryString["prompt"]
        if (-not $Prompt) { $Prompt = "Hello from MCP PowerShell Server!" }

        Write-Host "🧠 Sending prompt to Hugging Face: $Prompt"

        # Выполняем запрос к Hugging Face API
        $Body = @{ inputs = $Prompt } | ConvertTo-Json -Depth 3
        $Headers = @{
            "Authorization" = "Bearer $HF_TOKEN"
            "Content-Type"  = "application/json"
        }

        $HF_Response = Invoke-RestMethod -Uri "https://api-inference.huggingface.co/models/$Model" `
                                         -Headers $Headers `
                                         -Method POST `
                                         -Body $Body `
                                         -ErrorAction Stop

        # Отправляем ответ как MCP событие
        $json = ($HF_Response | ConvertTo-Json -Depth 6)
        Send-SSEEvent -Writer $Writer -EventType "message" -Data $json
        Write-Host "📤 Sent response"

    } catch {
        Send-SSEEvent -Writer $Writer -EventType "error" -Data $_.Exception.Message
        Write-Host "❌ Error: $($_.Exception.Message)"
    }

    # Закрываем соединение
    $Writer.Flush()
    $Response.Close()
}

