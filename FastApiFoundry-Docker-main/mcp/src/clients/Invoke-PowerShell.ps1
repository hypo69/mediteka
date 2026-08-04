# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: MCP HTTPS Server - PowerShell Test Client
# =============================================================================
# Description:
#   Sends a test PowerShell command to the MCP HTTPS server and prints the result.
#   Bypasses SSL certificate validation so it works with self-signed certs
#   used during local development.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\powershell.ps1
#
# File: mcp-powershell-servers/src/clients/powershell.ps1
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

# MCP server endpoint — change host/port to match your McpHttpsServer config
$Url   = "https://localhost:8443/execute"
# Bearer token must match the token configured in the server
$Token = "SuperSecretToken123"

# Authorization header required by the MCP HTTPS server
$Headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type"  = "application/json"
}

# The PowerShell command to execute on the server side
$Payload = @{
    command = "Get-Process | Select-Object -First 5 | ConvertTo-Json -Depth 3"
} | ConvertTo-Json -Depth 3

# -----------------------------------------------------------------------------
# Trust all certificates — required for self-signed certs in local dev
# In production, replace this with a proper certificate or use -SkipCertificateCheck
# -----------------------------------------------------------------------------
add-type @"
using System.Net;
using System.Security.Cryptography.X509Certificates;
public class TrustAllCertsPolicy : ICertificatePolicy {
    public bool CheckValidationResult(
        ServicePoint srvPoint, X509Certificate certificate,
        WebRequest request, int certificateProblem) {
        return true;
    }
}
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy

# --- main ---

try {
    $Response = Invoke-RestMethod -Uri $Url -Method Post -Headers $Headers -Body $Payload
    Write-Host "Response from MCP PowerShell Server:" -ForegroundColor Green
    $Response | ConvertTo-Json -Depth 5 | Out-String
} catch {
    Write-Host "Request error: $($_.Exception.Message)" -ForegroundColor Red
}
