# -*- coding: utf-8 -*-
param (
    [Parameter(Mandatory = $true)]
    [string]$Command,
    [string[]]$Arguments = @(),
    [Parameter(Mandatory = $true)]
    [string]$OutFile,
    [int]$TimeoutSec = 30
)

function Write-Json {
    param ($obj)
    ($obj | ConvertTo-Json -Compress) | Add-Content -Path $OutFile -Encoding utf8
}

$corr = [guid]::NewGuid().ToString()
$start = Get-Date

# Debug
Write-Host "Command: $Command"
Write-Host "Arguments: $Arguments"
Write-Host "OutFile: $OutFile"

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $Command
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

$proc.add_OutputDataReceived({
    param($s,$e)
    if ($e.Data) {
        Write-Json @{ ts = (Get-Date).ToString('o'); cid = $corr; stream = 'stdout'; msg = $e.Data }
        Write-Host "STDOUT: $($e.Data)"
    }
})

$proc.add_ErrorDataReceived({
    param($s,$e)
    if ($e.Data) {
        Write-Json @{ ts = (Get-Date).ToString('o'); cid = $corr; stream = 'stderr'; msg = $e.Data }
        Write-Host "STDERR: $($e.Data)"
    }
})

$null = $proc.Start()
$proc.BeginOutputReadLine()
$proc.BeginErrorReadLine()

$timedOut = -not $proc.WaitForExit($TimeoutSec * 1000)

if ($timedOut) {
    try { $proc.Kill() } catch {}
}

$end = Get-Date
$duration = [int](($end - $start).TotalMilliseconds)

Write-Json @{
    ts = (Get-Date).ToString('o'); cid = $corr; stream = 'meta'
    exit_code = if ($timedOut) { -999 } else { $proc.ExitCode }
    duration_ms = $duration; timed_out = $timedOut
}

Write-Host "Exit code: $($proc.ExitCode)"

exit $proc.ExitCode
