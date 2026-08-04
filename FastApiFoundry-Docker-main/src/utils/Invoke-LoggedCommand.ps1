# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Компактная обертка логирования команд
# =============================================================================
# Описание:
#   Асинхронный запуск процесса с записью вывода в JSON Lines формат.
#   Поддержка Correlation ID и принудительного завершения по таймауту.
#
# File: Invoke-LoggedCommand.ps1
# Version: 0.6.1
# Author: hypo69
# =============================================================================

param (
    [Parameter(Mandatory = $true)]
    [string]$Command,
    [string[]]$Arguments = @(),
    [Parameter(Mandatory = $true)]
    [string]$OutFile,
    [int]$TimeoutSec = 30
)

# Инициализация идентификатора корреляции
$corr = [guid]::NewGuid().ToString()
$start = Get-Date

function Write-Json {
    param ($obj)
    # Компактная запись JSON без лишних пробелов
    ($obj | ConvertTo-Json -Compress) | Add-Content -Path $OutFile -Encoding utf8
}

# Настройка параметров запуска процесса
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $Command
# If Arguments is a single string, split it; otherwise use as array
if ($Arguments -is [string] -and $Arguments -ne '') {
    $psi.Arguments = $Arguments
} elseif ($Arguments -is [array]) {
    $psi.Arguments = ($Arguments -join ' ')
}
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi

# Асинхронные обработчики потоков
$proc.add_OutputDataReceived({
    param($s,$e)
    if ($e.Data) {
        Write-Json @{ ts = (Get-Date).ToString('o'); cid = $corr; stream = 'stdout'; msg = $e.Data }
    }
})

$proc.add_ErrorDataReceived({
    param($s,$e)
    if ($e.Data) {
        Write-Json @{ ts = (Get-Date).ToString('o'); cid = $corr; stream = 'stderr'; msg = $e.Data }
    }
})

# Запуск и ожидание завершения
$null = $proc.Start()
$proc.BeginOutputReadLine()
$proc.BeginErrorReadLine()

$timedOut = -not $proc.WaitForExit($TimeoutSec * 1000)

if ($timedOut) {
    try { $proc.Kill() } catch {}
}

$end = Get-Date
$duration = [int](($end - $start).TotalMilliseconds)

# Запись финальных метаданных
Write-Json @{
    ts = (Get-Date).ToString('o'); cid = $corr; stream = 'meta'
    exit_code = if ($timedOut) { -999 } else { $proc.ExitCode }
    duration_ms = $duration; timed_out = $timedOut
}

exit $proc.ExitCode

