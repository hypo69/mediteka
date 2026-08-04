param([string]$Root, [string]$Config)

$llamaPidFile = Join-Path $env:TEMP 'aiassistant-llama.pid'

function Ensure-LlamaBin {
    $binDir = Join-Path $Root 'bin'
    $configPath = Join-Path $Root $Config
    $zips = Get-ChildItem -Path $binDir -Filter 'llama-*-bin-win-*.zip' | Sort-Object Name -Descending
    if (-not $zips) { return $null }
    $latestZip = $zips[0]
    $latestStem = [System.IO.Path]::GetFileNameWithoutExtension($latestZip.Name)
    $extractDir = Join-Path $binDir $latestStem
    $serverExe = Join-Path $extractDir 'llama-server.exe'
    if (-not (Test-Path $serverExe)) {
        Expand-Archive -Path $latestZip.FullName -DestinationPath $extractDir -Force
    }
    return $serverExe
}

function Start-LlamaServer {
    param([string]$ServerExe, [string]$ModelPath, [int]$Port)
    Write-Host "🦙 Запуск llama.cpp на порту $Port..." -ForegroundColor Cyan
    $proc = Start-Process -FilePath $ServerExe -ArgumentList "--model", $ModelPath, "--port", $Port, "--host", "127.0.0.1", "--log-disable" -PassThru -WindowStyle Minimized
    if ($proc) {
        $proc.Id | Out-File $llamaPidFile -Encoding UTF8
        for ($i = 1; $i -le 10; $i++) {
            Start-Sleep 2
            try {
                $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
                if ($r.StatusCode -eq 200) {
                    Write-Host "✅ llama.cpp запущен (PID: $($proc.Id))" -ForegroundColor Green
                    return $true
                }
            } catch {}
        }
    }
    return $false
}

Write-Host '🦙 Подготовка llama.cpp...' -ForegroundColor Cyan
$llamaModelPath = $null
$llamaAutoStart = $false
$llamaPort = 9780

try {
    $cfg = Get-Content (Join-Path $Root $Config) -Raw | ConvertFrom-Json
    if ($cfg.llama_cpp) {
        $llamaModelsDir = ($cfg.llama_cpp.models_dir -replace '^~', $env:USERPROFILE)
        if ($cfg.llama_cpp.default_model) {
            $llamaModelPath = Join-Path $llamaModelsDir $cfg.llama_cpp.default_model
        }
        $llamaAutoStart = [bool]$cfg.llama_cpp.auto_start
        $llamaPort = if ($cfg.llama_cpp.port) { [int]$cfg.llama_cpp.port } else { 9780 }
    }
} catch {}

if ($llamaModelPath -and $llamaAutoStart) {
    $llamaServerExe = Ensure-LlamaBin
    if ($llamaServerExe) {
        # Остановка старого процесса
        $conn = Get-NetTCPConnection -LocalPort $llamaPort -State Listen -ErrorAction SilentlyContinue
        if ($conn) { Stop-Process -Id $conn.OwningProcess -Force }
        
        if (Start-LlamaServer -ServerExe $llamaServerExe -ModelPath $llamaModelPath -Port $llamaPort) {
            $env:LLAMA_BASE_URL = "http://127.0.0.1:$llamaPort/v1"
        }
    }
}