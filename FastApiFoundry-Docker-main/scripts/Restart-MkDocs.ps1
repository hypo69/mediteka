# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Restart MkDocs Documentation Server
# =============================================================================
# Description:
#   Delegates to doc.ps1 in the project root, which handles stop/start/wait.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\restart-mkdocs.ps1
#
# File: scripts/restart-mkdocs.ps1
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

$ROOT = Split-Path -Parent $PSScriptRoot
& "$ROOT\doc.ps1"
