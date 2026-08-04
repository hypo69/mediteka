# -*- coding: utf-8 -*-
# Shared helpers for install.ps1 and scripts\Install\Step-*.ps1.

function Write-InstallLog {
    param(
        [string]$Message,
        [string]$Level = 'INFO'
    )

    try {
        if (-not (Test-Path $InstallLogDir)) {
            New-Item -ItemType Directory -Path $InstallLogDir -Force | Out-Null
        }
        $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        Add-Content -Path $InstallLogFile -Value "$ts | $($Level.ToUpper().PadRight(7)) | install | $Message" -Encoding UTF8
    } catch {
        # Logging must never break installation.
    }
}

function Resolve-Mode {
    param([string]$Raw)

    $n = $Raw.ToLower().Trim()
    switch ($n) {
        ''         { return 'prod'     }
        'prod'     { return 'prod'     }
        'qa'       { return 'qa'       }
        'debug'    { return 'debug'    }
        'qa+debug' { return 'qa+debug' }
        'debug+qa' { return 'qa+debug' }
        default    { throw "Unknown mode: '$Raw'. Valid: prod | qa | debug | qa+debug | debug+qa" }
    }
}

function Get-ModeFromFile {
    param([string]$ProjectRoot)

    $modeFile = Join-Path $ProjectRoot 'MODE'
    if (-not (Test-Path $modeFile)) { return '' }

    $line = Get-Content $modeFile |
            Where-Object { $_ -match '^\s*mode\s*=' } |
            Select-Object -First 1

    if (-not $line) { return '' }
    return ($line -split '=', 2)[1].Trim()
}

function Get-InstallScriptPath {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Name
    )

    return (Join-Path $Root "scripts\Install\$Name")
}

function Invoke-OptionalInstallScript {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Name,
        [Parameter(Mandatory=$true)]
        [string]$DisplayName,
        [scriptblock]$Invoke,
        [string]$MissingMessage,
        [string]$UnavailableMessage,
        [string]$LogName = $DisplayName
    )

    $scriptPath = Get-InstallScriptPath $Name
    if (-not (Test-Path $scriptPath)) {
        $message = if ($MissingMessage) { $MissingMessage } else { "  scripts\Install\$Name not found - skipping" }
        Write-Host $message -ForegroundColor Yellow
        Write-InstallLog "scripts\Install\$Name not found; skipping $LogName" 'WARNING'
        return
    }

    try {
        $global:LASTEXITCODE = 0
        & $Invoke $scriptPath
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  $DisplayName installer returned exit code $LASTEXITCODE - continuing" -ForegroundColor Yellow
            Write-InstallLog "$DisplayName installer returned exit code $LASTEXITCODE; continuing" 'ERROR'
        } else {
            Write-InstallLog "$DisplayName installer step completed"
        }
    } catch {
        Write-Host "  $DisplayName installer error: $_" -ForegroundColor Yellow
        if ($UnavailableMessage) {
            Write-Host "  $UnavailableMessage" -ForegroundColor Cyan
        }
        Write-InstallLog "$DisplayName installer error: $_; continuing" 'ERROR'
    }
}

function Stop-VenvProcesses {
    param([string]$VenvPath)

    Write-Host '  Stopping services on ports 9696 / 9697...' -ForegroundColor Gray

    foreach ($port in @(9696, 9697)) {
        $conn = netstat -ano 2>$null |
                Select-String ":$port\s" |
                Select-Object -First 1
        if ($conn) {
            $pid_ = ($conn -split '\s+')[-1]
            if ($pid_ -match '^\d+$') {
                Stop-Process -Id ([int]$pid_) -Force -ErrorAction SilentlyContinue
                Write-Host "  Killed PID $pid_ (port $port)" -ForegroundColor Gray
            }
        }
    }

    Get-Process -Name python, python3, python311 -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -like "$VenvPath*" } |
        Stop-Process -Force -ErrorAction SilentlyContinue

    Start-Sleep -Milliseconds 700
}

function Test-PreFlightRequirements {
    param([string]$ProjectRoot)

    Write-Host "`nВыполнение предварительных проверок (Pre-flight checks)..." -ForegroundColor Cyan

    $configFile = Join-Path $ProjectRoot 'config.json'
    if (-not (Test-Path $configFile)) {
        Write-Host '  config.json not found, skipping path checks.' -ForegroundColor Yellow
        return
    }

    $cfg = Get-Content $configFile -Raw | ConvertFrom-Json
    $dirs = $cfg.directories.PSObject.Properties

    foreach ($prop in $dirs) {
        $pathStr = $prop.Value
        $expandedPath = $pathStr.Replace('~', $env:USERPROFILE)
        $dirName = $prop.Name

        Write-Host "  Checking: $dirName ($expandedPath)" -ForegroundColor Gray

        if ($dirName -eq 'models') {
            $rootPath = Split-Path -Path $expandedPath -Qualifier
            if (-not $rootPath) { $rootPath = $env:SystemDrive }

            $drive = Get-PSDrive ($rootPath.Replace(':', ''))
            $freeGb = [math]::Round($drive.Free / 1GB, 2)

            if ($freeGb -lt 5.0) {
                Write-Host "  Not enough free space on $rootPath. Free: $freeGb GB, required: 5 GB" -ForegroundColor Red
                exit 1
            }
            Write-Host "  Free space: $freeGb GB" -ForegroundColor Green
        }

        if (-not (Test-Path $expandedPath)) {
            try {
                New-Item -ItemType Directory -Path $expandedPath -Force | Out-Null
                Write-Host '  Directory created' -ForegroundColor Green
            } catch {
                Write-Host "  Failed to create directory ${expandedPath}: $_" -ForegroundColor Red
                exit 1
            }
        }

        $testFile = Join-Path $expandedPath ".install_test_$(Get-Random)"
        try {
            'test' | Out-File $testFile -ErrorAction Stop
            Remove-Item $testFile -ErrorAction Stop
            Write-Host '  Write access confirmed' -ForegroundColor Green
        } catch {
            Write-Host "  No write access to $expandedPath" -ForegroundColor Red
            exit 1
        }
    }
    Write-Host "Pre-flight checks completed.`n" -ForegroundColor Green
}

function Ensure-LMStudioConfig {
    param([string]$ConfigPath)

    if (-not (Test-Path $ConfigPath)) { return }

    try {
        $cfgObj = Get-Content $ConfigPath -Raw | ConvertFrom-Json
        if (-not $cfgObj.PSObject.Properties['lmstudio']) {
            $cfgObj | Add-Member -NotePropertyName 'lmstudio' -NotePropertyValue ([ordered]@{
                base_url = 'http://localhost:1234'
                api_key = ''
                default_model = ''
                request_timeout_sec = 300
            })
            $cfgObj | ConvertTo-Json -Depth 10 | Set-Content $ConfigPath -Encoding UTF8
            Write-Host '  config.json: lmstudio section added' -ForegroundColor Green
        } else {
            $changed = $false
            foreach ($field in @(
                @{ Name='base_url';            Value='http://localhost:1234' },
                @{ Name='api_key';             Value='' },
                @{ Name='default_model';       Value='' },
                @{ Name='request_timeout_sec'; Value=300 }
            )) {
                if (-not $cfgObj.lmstudio.PSObject.Properties[$field.Name]) {
                    $cfgObj.lmstudio | Add-Member -NotePropertyName $field.Name -NotePropertyValue $field.Value
                    $changed = $true
                }
            }
            if ($changed) {
                $cfgObj | ConvertTo-Json -Depth 10 | Set-Content $ConfigPath -Encoding UTF8
                Write-Host '  config.json: lmstudio defaults completed' -ForegroundColor Green
            } else {
                Write-Host '  config.json: lmstudio section already present' -ForegroundColor Gray
            }
        }
    } catch {
        Write-Host "  Could not update lmstudio config: $_" -ForegroundColor Yellow
    }
}

function Ensure-OllamaConfig {
    param([string]$ConfigPath)

    if (-not (Test-Path $ConfigPath)) { return }

    try {
        $cfgObj = Get-Content $ConfigPath -Raw | ConvertFrom-Json
        if (-not $cfgObj.PSObject.Properties['ollama']) {
            $cfgObj | Add-Member -NotePropertyName 'ollama' -NotePropertyValue ([ordered]@{
                base_url    = 'http://localhost:11434'
                temperature = 0.7
                top_p       = 0.9
                top_k       = 50
                max_tokens  = 2048
            })
            $cfgObj | ConvertTo-Json -Depth 10 | Set-Content $ConfigPath -Encoding UTF8
            Write-Host '  config.json: ollama section added' -ForegroundColor Green
        } else {
            $changed = $false
            foreach ($field in @(
                @{ Name='base_url';    Value='http://localhost:11434' },
                @{ Name='temperature'; Value=0.7 },
                @{ Name='top_p';       Value=0.9 },
                @{ Name='top_k';       Value=50 },
                @{ Name='max_tokens';  Value=2048 }
            )) {
                if (-not $cfgObj.ollama.PSObject.Properties[$field.Name]) {
                    $cfgObj.ollama | Add-Member -NotePropertyName $field.Name -NotePropertyValue $field.Value
                    $changed = $true
                }
            }
            if ($changed) {
                $cfgObj | ConvertTo-Json -Depth 10 | Set-Content $ConfigPath -Encoding UTF8
                Write-Host '  config.json: ollama defaults completed' -ForegroundColor Green
            } else {
                Write-Host '  config.json: ollama section already present' -ForegroundColor Gray
            }
        }
    } catch {
        Write-Host "  Could not update ollama config: $_" -ForegroundColor Yellow
    }
}

function Ensure-OpenCodeConfig {
    param([string]$ConfigPath)

    if (-not (Test-Path $ConfigPath)) { return }

    try {
        $cfgObj = Get-Content $ConfigPath -Raw | ConvertFrom-Json
        if (-not $cfgObj.PSObject.Properties['opencode']) {
            $cfgObj | Add-Member -NotePropertyName 'opencode' -NotePropertyValue ([ordered]@{
                enabled    = $true
                auto_start = $true
                host       = '0.0.0.0'
                port       = 9699
                command    = 'opencode'
            })
            $cfgObj | ConvertTo-Json -Depth 10 | Set-Content $ConfigPath -Encoding UTF8
            Write-Host '  config.json: opencode section added' -ForegroundColor Green
        } else {
            $changed = $false
            foreach ($field in @(
                @{ Name='enabled';    Value=$true },
                @{ Name='auto_start'; Value=$true },
                @{ Name='host';       Value='0.0.0.0' },
                @{ Name='port';       Value=9699 },
                @{ Name='command';    Value='opencode' }
            )) {
                if (-not $cfgObj.opencode.PSObject.Properties[$field.Name]) {
                    $cfgObj.opencode | Add-Member -NotePropertyName $field.Name -NotePropertyValue $field.Value
                    $changed = $true
                }
            }
            if ($changed) {
                $cfgObj | ConvertTo-Json -Depth 10 | Set-Content $ConfigPath -Encoding UTF8
                Write-Host '  config.json: opencode defaults completed' -ForegroundColor Green
            } else {
                Write-Host '  config.json: opencode section already present' -ForegroundColor Gray
            }
        }
    } catch {
        Write-Host "  Could not update opencode config: $_" -ForegroundColor Yellow
    }
}
