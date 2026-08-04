# -*- coding: utf-8 -*-
# Compatibility wrapper. The installer implementation lives in scripts\Install.

param(
    [int]$TimeoutSec = 60,
    [switch]$Verbose
)

$target = Join-Path $PSScriptRoot 'Install\ReinstallFoundry.ps1'
& $target -TimeoutSec $TimeoutSec -Verbose:$Verbose
exit $LASTEXITCODE
