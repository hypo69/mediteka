# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: MCP WP-CLI Server - PowerShell Test Client
# =============================================================================
# Description:
#   Sends a JSON-RPC 2.0 MCP request to the WP-CLI MCP server over HTTPS.
#   Calls the 'run-wp-cli' tool with 'user list' to retrieve WordPress users.
#   Bypasses SSL certificate validation for local development with self-signed certs.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\wpcli.ps1
#
# File: mcp-powershell-servers/src/clients/wpcli.ps1
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

#region Server and auth settings

# ⚠️ Replace with the actual URL and token of your MCP HTTP server
$Url   = "https://localhost:8443/execute"
$Token = "SuperSecretToken123"

# Authorization header required by the MCP HTTPS server
$Headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type"  = "application/json"
}

#endregion

#region Build the MCP JSON-RPC request

# ⚠️ Replace with the actual path to your WordPress installation
$WordPressPath = "E:\xampp\htdocs\domains\davidka.net\public_html"

# JSON-RPC 2.0 envelope — calls the 'run-wp-cli' tool registered on the server
$MCPRequest = @{
    jsonrpc = "2.0"
    id      = (New-Guid).ToString()   # unique request ID for correlation
    method  = "tools/call"
    params  = @{
        name      = "run-wp-cli"
        arguments = @{
            # WP-CLI arguments passed to 'wp <commandArguments>'
            commandArguments = "user list"
            workingDirectory = $WordPressPath
        }
    }
}

$Payload = $MCPRequest | ConvertTo-Json -Depth 5

#endregion

#region Trust self-signed certificates (local dev only)

# In production use a valid certificate or the -SkipCertificateCheck parameter
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

#endregion

#region Send request and handle response

Write-Host "Sending MCP request to $Url..." -ForegroundColor Cyan
Write-Host "Command: wp user list in $WordPressPath" -ForegroundColor DarkCyan

try {
    $Response = Invoke-RestMethod -Uri $Url -Method Post -Headers $Headers -Body $Payload -ContentType "application/json" -ErrorAction Stop

    Write-Host "`n--- MCP Server Response ---" -ForegroundColor Green
    $Response | ConvertTo-Json -Depth 5 | Write-Host

    # Surface any application-level error returned by the server
    if ($Response.error -ne $null) {
        Write-Host "`nServer error (Code $($Response.error.code)): $($Response.error.message)" -ForegroundColor Red
    }

    # Extract the WP-CLI text output from the MCP content array
    if ($Response.result -ne $null -and $Response.result.content -ne $null) {
        $wpCliResult = $Response.result.content | Where-Object { $_.type -eq 'text' }
        Write-Host "`n--- WP-CLI Output ---" -ForegroundColor Yellow
        $wpCliResult.text -join "`n" | Write-Host
    }

} catch {
    # Network-level or HTTP 5xx error
    Write-Host "`nRequest failed:" -ForegroundColor Red
    Write-Host "$($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response -ne $null) {
        Write-Host "HTTP Status: $($_.Exception.Response.StatusCode.Value__) $($_.Exception.Response.StatusDescription)" -ForegroundColor Red
    }
}

#endregion
