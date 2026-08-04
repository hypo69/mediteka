<# 
.SYNOPSIS
Production-grade Windows OS diagnostic toolkit.

.DESCRIPTION
Collects Windows telemetry, writes a lightweight JSONL time-series store,
runs a rule and correlation engine, calculates a health score, and emits
JSON, HTML, and RST reports.
#>

[CmdletBinding()]
param(
    [string]$OutputDir = ".\logs\os_diagnostic",
    [string]$StorePath = "",
    [string]$JsonReportPath = "",
    [string]$HtmlReportPath = "",
    [string]$RstReportPath = "",
    [int]$WindowHours = 24,
    [switch]$NoStore,
    [switch]$SkipEvents
)

$ErrorActionPreference = "Continue"

function New-DirectoryIfMissing {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function ConvertTo-SafeJson {
    param([Parameter(ValueFromPipeline = $true)]$InputObject, [int]$Depth = 8)
    process {
        $InputObject | ConvertTo-Json -Depth $Depth -Compress
    }
}

function New-Finding {
    param(
        [ValidateSet("info", "warning", "error", "critical")][string]$Severity,
        [string]$Code,
        [string]$Title,
        [string]$Message,
        [string]$Evidence = "",
        [string]$Recommendation = ""
    )

    [pscustomobject]@{
        severity       = $Severity
        code           = $Code
        title          = $Title
        message        = $Message
        evidence       = $Evidence
        recommendation = $Recommendation
    }
}

function Get-SystemSnapshot {
    param([bool]$IncludeEvents = $true)

    $timestamp = (Get-Date).ToUniversalTime().ToString("o")
    $os = Get-CimInstance Win32_OperatingSystem
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    $disks = Get-PSDrive -PSProvider FileSystem | ForEach-Object {
        $total = $_.Used + $_.Free
        [pscustomobject]@{
            name             = $_.Name
            used_gb          = [math]::Round($_.Used / 1GB, 2)
            free_gb          = [math]::Round($_.Free / 1GB, 2)
            total_gb         = [math]::Round($total / 1GB, 2)
            free_percent     = if ($total -gt 0) { [math]::Round(($_.Free / $total) * 100, 2) } else { 0 }
        }
    }

    $topCpu = Get-Process |
        Sort-Object CPU -Descending |
        Select-Object -First 10 Name, Id, CPU, @{Name = "mem_mb"; Expression = { [math]::Round($_.WorkingSet / 1MB, 1) }}

    $topMemory = Get-Process |
        Sort-Object WorkingSet -Descending |
        Select-Object -First 10 Name, Id, CPU, @{Name = "mem_mb"; Expression = { [math]::Round($_.WorkingSet / 1MB, 1) }}

    $services = Get-Service | Group-Object Status | ForEach-Object {
        [pscustomobject]@{ status = [string]$_.Name; count = $_.Count }
    }

    $startupCount = (Get-CimInstance Win32_StartupCommand -ErrorAction SilentlyContinue | Measure-Object).Count
    $networkAdapters = Get-NetAdapter -ErrorAction SilentlyContinue |
        Where-Object Status -eq "Up" |
        Select-Object Name, InterfaceDescription, LinkSpeed

    $defender = $null
    try {
        $defender = Get-MpComputerStatus -ErrorAction Stop |
            Select-Object AMServiceEnabled, AntivirusEnabled, AntispywareEnabled,
                RealTimeProtectionEnabled, AntivirusSignatureLastUpdated, QuickScanEndTime, FullScanEndTime
    } catch {
        $defender = [pscustomobject]@{ error = $_.Exception.Message }
    }

    $updates = $null
    try {
        $updates = [pscustomobject]@{
            service = Get-Service wuauserv -ErrorAction Stop |
                Select-Object Name, DisplayName, Status, StartType
            recent_hotfixes = Get-HotFix -ErrorAction SilentlyContinue |
                Sort-Object InstalledOn -Descending |
                Select-Object -First 10 HotFixID, Description, InstalledOn
        }
    } catch {
        $updates = [pscustomobject]@{ error = $_.Exception.Message }
    }

    $events = @()
    if ($IncludeEvents) {
        try {
            $events = Get-WinEvent -FilterHashtable @{ LogName = "System"; Level = 1, 2, 3 } -MaxEvents 100 -ErrorAction Stop |
                Select-Object TimeCreated, Id, ProviderName, LevelDisplayName, Message
        } catch {
            $events = @([pscustomobject]@{ error = $_.Exception.Message })
        }
    }

    [pscustomobject]@{
        timestamp        = $timestamp
        host             = $env:COMPUTERNAME
        os               = [pscustomobject]@{
            caption         = $os.Caption
            version         = $os.Version
            uptime_hours    = [math]::Round((New-TimeSpan $os.LastBootUpTime).TotalHours, 1)
            total_ram_gb    = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
            free_ram_gb     = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
            free_ram_pct    = [math]::Round(($os.FreePhysicalMemory / $os.TotalVisibleMemorySize) * 100, 2)
        }
        cpu              = [pscustomobject]@{
            name         = $cpu.Name
            cores        = $cpu.NumberOfCores
            load_percent = $cpu.LoadPercentage
        }
        disks            = @($disks)
        processes        = [pscustomobject]@{ top_cpu = @($topCpu); top_memory = @($topMemory) }
        services         = @($services)
        startup_count    = $startupCount
        network_adapters = @($networkAdapters)
        defender         = $defender
        windows_update   = $updates
        events           = @($events)
    }
}

function Read-TimeSeries {
    param([string]$Path, [int]$WindowHours)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return @()
    }

    $cutoff = (Get-Date).ToUniversalTime().AddHours(-1 * $WindowHours)
    $rows = @()
    Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue | ForEach-Object {
        if (-not $_.Trim()) { return }
        try {
            $item = $_ | ConvertFrom-Json
            if ([datetime]$item.timestamp -ge $cutoff) {
                $rows += $item
            }
        } catch {
        }
    }
    return $rows
}

function Write-TimeSeries {
    param([string]$Path, $Snapshot)
    $line = $Snapshot | ConvertTo-SafeJson -Depth 12
    Add-Content -LiteralPath $Path -Encoding UTF8 -Value $line
}

function Invoke-RuleEngine {
    param($Snapshot)

    $findings = New-Object System.Collections.Generic.List[object]

    if ($Snapshot.cpu.load_percent -ge 90) {
        $findings.Add((New-Finding error "CPU_HIGH" "High CPU load" "CPU load is above 90%." "$($Snapshot.cpu.load_percent)%" "Inspect top CPU processes and scheduled tasks."))
    } elseif ($Snapshot.cpu.load_percent -ge 75) {
        $findings.Add((New-Finding warning "CPU_ELEVATED" "Elevated CPU load" "CPU load is above 75%." "$($Snapshot.cpu.load_percent)%" "Watch the trend and inspect top CPU processes."))
    }

    if ($Snapshot.os.free_ram_pct -lt 10) {
        $findings.Add((New-Finding error "RAM_LOW" "Low free RAM" "Free RAM is below 10%." "$($Snapshot.os.free_ram_gb) GB free" "Inspect top memory processes and consider restart or capacity increase."))
    } elseif ($Snapshot.os.free_ram_pct -lt 20) {
        $findings.Add((New-Finding warning "RAM_PRESSURE" "RAM pressure" "Free RAM is below 20%." "$($Snapshot.os.free_ram_gb) GB free" "Review memory-heavy processes."))
    }

    foreach ($disk in $Snapshot.disks) {
        if ($disk.total_gb -le 0) {
            continue
        }
        if ($disk.free_percent -lt 10) {
            $findings.Add((New-Finding critical "DISK_LOW_$($disk.name)" "Low disk space" "Drive $($disk.name) has less than 10% free space." "$($disk.free_gb) GB free" "Run cleanup dry-run and move/delete large files."))
        } elseif ($disk.free_percent -lt 20) {
            $findings.Add((New-Finding warning "DISK_WARN_$($disk.name)" "Disk space warning" "Drive $($disk.name) has less than 20% free space." "$($disk.free_gb) GB free" "Plan cleanup before it becomes critical."))
        }
    }

    if ($Snapshot.defender.PSObject.Properties.Name -contains "RealTimeProtectionEnabled" -and -not $Snapshot.defender.RealTimeProtectionEnabled) {
        $findings.Add((New-Finding critical "DEFENDER_REALTIME_OFF" "Defender realtime protection is off" "Microsoft Defender realtime protection is disabled." "" "Re-enable realtime protection unless intentionally managed by another AV."))
    }

    $eventErrors = @($Snapshot.events | Where-Object { $_.LevelDisplayName -in @("Critical", "Error") })
    if ($eventErrors.Count -ge 20) {
        $findings.Add((New-Finding error "EVENT_ERROR_BURST" "Many recent system errors" "System log has many recent error or critical events." "$($eventErrors.Count) events in latest sample" "Group events by provider and correlate with updates, services, and restarts."))
    } elseif ($eventErrors.Count -ge 5) {
        $findings.Add((New-Finding warning "EVENT_ERRORS" "Recent system errors" "System log contains recent errors." "$($eventErrors.Count) events in latest sample" "Review top providers and repeated event IDs."))
    }

    return $findings.ToArray()
}

function Invoke-CorrelationEngine {
    param($Snapshot, [array]$History)

    $signals = New-Object System.Collections.Generic.List[object]
    if ($History.Count -ge 2) {
        $oldest = $History[0]
        $latest = $Snapshot
        foreach ($disk in $latest.disks) {
            $oldDisk = @($oldest.disks | Where-Object name -eq $disk.name | Select-Object -First 1)
            if ($oldDisk.Count -gt 0) {
                $delta = [math]::Round($disk.free_gb - $oldDisk[0].free_gb, 2)
                if ($delta -lt -2) {
                    $signals.Add([pscustomobject]@{
                        type = "trend"
                        code = "DISK_FREE_FALLING"
                        message = "Drive $($disk.name) free space dropped by $([math]::Abs($delta)) GB in the selected window."
                    })
                }
            }
        }
    }

    $providerGroups = @($Snapshot.events |
        Where-Object { $_.ProviderName } |
        Group-Object ProviderName |
        Sort-Object Count -Descending |
        Select-Object -First 5)

    foreach ($group in $providerGroups) {
        if ($group.Count -ge 3) {
            $signals.Add([pscustomobject]@{
                type = "event_correlation"
                code = "REPEATED_EVENT_PROVIDER"
                message = "$($group.Name) appears $($group.Count) times in recent events."
            })
        }
    }

    return $signals.ToArray()
}

function Get-HealthScore {
    param([array]$Findings)
    $penalty = 0
    foreach ($finding in $Findings) {
        switch ($finding.severity) {
            "critical" { $penalty += 30 }
            "error"    { $penalty += 18 }
            "warning"  { $penalty += 8 }
            default    { $penalty += 1 }
        }
    }
    return [math]::Max(0, 100 - $penalty)
}

function ConvertTo-HtmlReport {
    param($Report)
    $rows = ($Report.findings | ForEach-Object {
        "<tr><td>$($_.severity)</td><td>$($_.code)</td><td>$($_.title)</td><td>$($_.message)</td><td>$($_.recommendation)</td></tr>"
    }) -join "`n"

    @"
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>OS Diagnostic Report</title>
  <style>
    body { font-family: Segoe UI, Arial, sans-serif; margin: 24px; color: #1f2937; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #d1d5db; padding: 8px; vertical-align: top; }
    th { background: #f3f4f6; text-align: left; }
    .score { font-size: 32px; font-weight: 700; }
  </style>
</head>
<body>
  <h1>OS Diagnostic Report</h1>
  <p><strong>Host:</strong> $($Report.host) | <strong>Timestamp:</strong> $($Report.timestamp)</p>
  <p class="score">Health score: $($Report.health_score)</p>
  <h2>Findings</h2>
  <table>
    <thead><tr><th>Severity</th><th>Code</th><th>Title</th><th>Message</th><th>Recommendation</th></tr></thead>
    <tbody>$rows</tbody>
  </table>
  <h2>Reasoning summary</h2>
  <pre>$($Report.reasoning_summary)</pre>
</body>
</html>
"@
}

function ConvertTo-RstReport {
    param($Report)
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("OS Diagnostic Report")
    $lines.Add("====================")
    $lines.Add("")
    $lines.Add("Metadata")
    $lines.Add("--------")
    $lines.Add("")
    $lines.Add("* Host: $($Report.host)")
    $lines.Add("* Timestamp: $($Report.timestamp)")
    $lines.Add("* Health score: $($Report.health_score)")
    $lines.Add("")
    $lines.Add("Findings")
    $lines.Add("--------")
    $lines.Add("")
    foreach ($finding in $Report.findings) {
        $lines.Add("* [$($finding.severity)] $($finding.code): $($finding.title)")
        $lines.Add("  $($finding.message)")
        if ($finding.recommendation) {
            $lines.Add("  Recommendation: $($finding.recommendation)")
        }
    }
    if ($Report.findings.Count -eq 0) {
        $lines.Add("* No rule findings.")
    }
    $lines.Add("")
    $lines.Add("Correlation Signals")
    $lines.Add("-------------------")
    $lines.Add("")
    foreach ($signal in $Report.correlation_signals) {
        $lines.Add("* $($signal.code): $($signal.message)")
    }
    if ($Report.correlation_signals.Count -eq 0) {
        $lines.Add("* No correlation signals.")
    }
    $lines.Add("")
    $lines.Add("Reasoning Summary")
    $lines.Add("-----------------")
    $lines.Add("")
    $lines.Add($Report.reasoning_summary)
    return ($lines -join "`n")
}

New-DirectoryIfMissing -Path $OutputDir
if (-not $StorePath) { $StorePath = Join-Path $OutputDir "os_timeseries.jsonl" }
if (-not $JsonReportPath) { $JsonReportPath = Join-Path $OutputDir "os_diagnostic_report.json" }
if (-not $HtmlReportPath) { $HtmlReportPath = Join-Path $OutputDir "os_diagnostic_report.html" }
if (-not $RstReportPath) { $RstReportPath = Join-Path $OutputDir "os_diagnostic_report.rst" }

$snapshot = Get-SystemSnapshot -IncludeEvents:(-not $SkipEvents)
$historyBeforeWrite = Read-TimeSeries -Path $StorePath -WindowHours $WindowHours
if (-not $NoStore) {
    Write-TimeSeries -Path $StorePath -Snapshot $snapshot
}
$history = @($historyBeforeWrite) + @($snapshot)
$findings = Invoke-RuleEngine -Snapshot $snapshot
$correlationSignals = Invoke-CorrelationEngine -Snapshot $snapshot -History $history
$healthScore = Get-HealthScore -Findings $findings

$summary = if ($findings.Count -eq 0) {
    "No critical rule findings. Continue collecting time-series data for trend analysis."
} else {
    $severityRank = @{critical = 4; error = 3; warning = 2; info = 1}
    $highest = @($findings | Sort-Object @{Expression = { $severityRank[$_.severity] }} -Descending | Select-Object -First 1)[0]
    "Found $($findings.Count) issue(s). Highest severity: $($highest.severity)."
}

$report = [pscustomobject]@{
    schema_version       = "1.0"
    timestamp            = $snapshot.timestamp
    host                 = $snapshot.host
    health_score         = $healthScore
    findings             = @($findings)
    correlation_signals  = @($correlationSignals)
    reasoning_summary    = $summary
    snapshot             = $snapshot
    history_window_hours = $WindowHours
    store_path           = (Resolve-Path -LiteralPath $StorePath -ErrorAction SilentlyContinue).Path
}

$json = $report | ConvertTo-Json -Depth 14
Set-Content -LiteralPath $JsonReportPath -Encoding UTF8 -Value $json
Set-Content -LiteralPath $HtmlReportPath -Encoding UTF8 -Value (ConvertTo-HtmlReport -Report $report)
Set-Content -LiteralPath $RstReportPath -Encoding UTF8 -Value (ConvertTo-RstReport -Report $report)

$report | ConvertTo-Json -Depth 14 -Compress
