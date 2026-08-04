# Foundry Startup Fix Design

## Overview

This bugfix addresses critical startup and control issues with the Foundry Local AI service integration. The user reports two main problems:

1. **Startup Detection Failure**: Foundry doesn't start automatically when running `start.ps1`, with logs showing "Foundry не обнаружен" (Foundry not found) and "Foundry недоступен - функции ИИ будут отключены" (Foundry unavailable - AI features disabled)

2. **UI Toggle Switch Failure**: The UI toggle switch in the Foundry tab doesn't work - clicking it doesn't change state

Investigation revealed:
- The frontend JavaScript calls `/foundry/stop` endpoint but this endpoint doesn't exist in the backend
- The `/foundry/start` endpoint exists but may not be working correctly
- The `Get-FoundryPort` function in start.ps1 may have issues detecting the Foundry service

**Fix Strategy**:
1. Add the missing `/foundry/stop` endpoint to `src/api/endpoints/install.py` (or ensure it's properly mounted from foundry_management.py)
2. Fix the `/foundry/start` endpoint to properly detect the started service
3. Improve the `Get-FoundryPort` function in `start.ps1` to correctly detect Foundry

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - Foundry service fails to start or be detected properly
- **Property (P)**: The desired behavior when Foundry is started - service should be detected on the correct port and UI should update
- **Preservation**: Existing functionality that must remain unchanged - manual Foundry start, other AI backends, config loading
- **Get-FoundryPort**: PowerShell function in start.ps1 that detects Foundry service port by scanning for Inference.Service.Agent process
- **foundry service start/stop**: Foundry CLI commands to control the service lifecycle
- **foundry_management.py**: API router with /foundry endpoints including /start and /stop
- **install.py**: API router with minimal /foundry/start endpoint that lacks proper detection

## Bug Details

### Bug Condition

The bug manifests when:
1. `start.ps1` is executed with `foundry_auto_start=true` but Foundry is not running
2. User clicks the Foundry toggle switch in the UI to start/stop the service
3. The system cannot detect the Foundry service on the correct port

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type StartContext (contains foundry_auto_start, current_process_state)
  OUTPUT: boolean
  
  RETURN (input.foundry_auto_start = true AND input.current_process_state = "not_running")
         OR (input.ui_action = "toggle_click" AND input.endpoint_missing = true)
         OR (input.service_started = true AND input.port_detection = false)
END FUNCTION
```

### Examples

- **Example 1**: User runs `start.ps1` with `foundry_auto_start=true`, Foundry service starts but `Get-FoundryPort` returns null, system shows "Foundry не обнаружен"
- **Example 2**: User clicks Foundry toggle switch to stop, frontend calls `/foundry/stop` endpoint which doesn't exist in install.py, 404 error, toggle state unchanged
- **Example 3**: User clicks Foundry toggle switch to start, `/foundry/start` endpoint exists but doesn't wait for service to be ready, returns success but service not yet available
- **Edge Case**: Foundry service is already running on a different port, system should detect and use existing service (this should NOT trigger the bug condition)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Manual Foundry service start via `foundry service start` should continue to work
- Foundry models should continue to load and unload correctly
- Other AI backends (HuggingFace, llama.cpp, Ollama) should remain unaffected
- Config loading from config.json should continue to work
- Environment variable FOUNDRY_BASE_URL should continue to be set correctly

**Scope:**
All inputs that do NOT involve Foundry auto-start or UI toggle actions should be completely unaffected by this fix. This includes:
- Manual Foundry service management
- Other AI model backends
- RAG system operations
- Configuration management

## Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Missing /foundry/stop endpoint in install.py**: The install.py router has a minimal `/foundry/start` endpoint but lacks the `/foundry/stop` endpoint that the frontend JavaScript expects to call

2. **Incorrect port detection in Get-FoundryPort**: The PowerShell function may not be correctly identifying the Foundry process or may be using an incorrect API endpoint for health checks

3. **Missing service readiness detection in /foundry/start**: The start endpoint in install.py starts the service but doesn't wait for it to be ready or verify it's actually running

4. **Endpoint routing issue**: The foundry_management.py router has both /start and /stop endpoints, but they may not be properly mounted or the frontend may be calling the wrong endpoint

## Correctness Properties

Property 1: Foundry Start/Stop Toggle Works

_For any_ UI toggle click action, the fixed code SHALL call the appropriate /foundry/start or /foundry/stop endpoint, execute the corresponding Foundry CLI command, and update the UI to reflect the new state.

**Validates: Requirements 2.2, 2.3**

Property 2: Startup Detection Works

_For any_ Foundry service start command, the fixed code SHALL wait for the service to be ready and correctly detect the running service on the appropriate port, setting FOUNDRY_BASE_URL correctly.

**Validates: Requirements 2.1**

Property 3: Error Handling

_For any_ Foundry CLI command execution, the fixed code SHALL return appropriate error messages when the Foundry CLI is not found or when the service fails to start, without crashing the application.

**Validates: Requirements 2.1, 2.2, 2.3**

## Fix Implementation

### Changes Required

**File 1**: `src/api/endpoints/install.py`

**Function**: `start_foundry()` (existing), add `stop_foundry()` (new)

**Specific Changes**:

1. **Add /foundry/stop endpoint to install.py**:
   - Add a new POST endpoint `/foundry/stop` that calls `foundry service stop`
   - Return appropriate success/error response
   - This endpoint should mirror the functionality in foundry_management.py

2. **Improve /foundry/start endpoint**:
   - Add service readiness detection after starting
   - Poll for service availability using the same logic as Get-FoundryPort
   - Return port information in response for UI to update FOUNDRY_BASE_URL

**File 2**: `start.ps1`

**Function**: `Get-FoundryPort` (existing)

**Specific Changes**:

1. **Improve port detection logic**:
   - Verify the process name pattern matches "Inference.Service.Agent" correctly
   - Add additional health check endpoint verification
   - Handle cases where multiple ports are listening
   - Add timeout handling for health checks

2. **Add fallback detection**:
   - If process-based detection fails, try common Foundry ports (50477, 50478)
   - Add explicit API endpoint check for /v1/models

**File 3**: `src/api/endpoints/foundry_management.py`

**Function**: Already has complete implementation

**Specific Changes**:
- Verify this router is properly mounted in app.py (it is - foundry_mgmt_router)
- Ensure frontend is calling the correct endpoint path (/api/v1/foundry/start vs /api/v1/install/foundry/start)

### Implementation Details

**install.py - Add stop_foundry function**:
```python
@api_router.post("/foundry/stop")
async def stop_foundry() -> dict:
    """Stop the Foundry Local service.

    Returns:
        dict — success flag or error message.
    """
    try:
        subprocess.Popen(["foundry", "service", "stop"])
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**install.py - Improved start_foundry function**:
```python
@api_router.post("/foundry/start")
async def start_foundry() -> dict:
    """Start the Foundry Local service with readiness detection.

    Returns:
        dict — success flag, port, and error message if applicable.
    """
    import time
    
    try:
        # Start the service
        subprocess.Popen(["foundry", "service", "start"])
        
        # Wait for service to be ready (max 30 seconds)
        for i in range(15):  # 15 attempts * 2 seconds = 30 seconds
            time.sleep(2)
            port = _detect_foundry_port()
            if port:
                return {
                    "success": True,
                    "port": port,
                    "url": f"http://localhost:{port}/v1/"
                }
        
        return {
            "success": False,
            "error": "Foundry service started but not detected within 30 seconds"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _detect_foundry_port() -> Optional[int]:
    """Detect Foundry service port using same logic as start.ps1."""
    import subprocess
    import json
    
    try:
        # Get process info
        result = subprocess.run(
            ["powershell", "-Command", 
             "Get-Process | Where-Object { $_.ProcessName -like 'Inference.Service.Agent*' } | Select-Object Id"],
            capture_output=True, text=True, timeout=5
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            return None
        
        # Parse process ID
        pid = int(result.stdout.strip())
        
        # Get listening ports for this process
        result = subprocess.run(
            ["powershell", "-Command",
             f"netstat -ano | Select-String '{pid}' | Select-String 'LISTENING'"],
            capture_output=True, text=True, timeout=5
        )
        
        if result.returncode != 0:
            return None
        
        # Parse port from netstat output
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if ':' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    port_str = parts[-1].split()[0]
                    try:
                        port = int(port_str)
                        # Verify it's Foundry API
                        import urllib.request
                        req = urllib.request.Request(
                            f"http://127.0.0.1:{port}/v1/models",
                            headers={'User-Agent': 'Python'}
                        )
                        with urllib.request.urlopen(req, timeout=2) as response:
                            if response.status == 200:
                                return port
                    except (ValueError, Exception):
                        continue
        
        return None
    except Exception:
        return None
```

**start.ps1 - Improved Get-FoundryPort function**:
```powershell
<#
.SYNOPSIS
    Поиск TCP-порта службы инференса Foundry.
    Обнаружение активного порта Foundry AI.
.DESCRIPTION
    Поиск процесса 'Inference.Service.Agent', сканирование портов LISTENING
    и проверка через API запрос к /v1/models.
.OUTPUTS
    string — Номер порта или $null.
#>
function Get-FoundryPort {
    # Try process-based detection first
    $foundryProcess = Get-Process | Where-Object { $_.ProcessName -like "Inference.Service.Agent*" }
    if (-not $foundryProcess) { 
        # Fallback: try common Foundry ports
        $commonPorts = @(50477, 50478, 50479)
        foreach ($port in $commonPorts) {
            try {
                $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/v1/models" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    Write-Host "✅ Foundry API detected on common port $port" -ForegroundColor Green
                    return $port
                }
            } catch { }
        }
        return $null
    }
    
    # Process-based detection
    $netstatOutput = netstat -ano | Select-String "$($foundryProcess.Id)" | Select-String "LISTENING"
    foreach ($line in $netstatOutput) {
        if ($line -match ':(\d+)\s') {
            $port = $matches[1]
            try {
                $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/v1/models" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    Write-Host "✅ API Foundry найден на порту $port" -ForegroundColor Green
                    return $port
                }
            } catch { }
        }
    }
    
    # Fallback: try common ports if process-based detection failed
    $commonPorts = @(50477, 50478, 50479)
    foreach ($port in $commonPorts) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/v1/models" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Foundry API detected on fallback port $port" -ForegroundColor Green
                return $port
            }
        } catch { }
    }
    
    return $null
}
```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that simulate Foundry startup scenarios and UI toggle actions, asserting that the correct endpoints are called and the service is properly detected.

**Test Cases**:
1. **Auto-start Test**: Run start.ps1 with foundry_auto_start=true, verify Foundry is detected (will fail on unfixed code)
2. **Stop Endpoint Test**: Call /foundry/stop endpoint, verify it returns 200 and service stops (will fail on unfixed code)
3. **Start Endpoint Test**: Call /foundry/start endpoint, verify it returns port and service is ready (will fail on unfixed code)
4. **Port Detection Test**: Test Get-FoundryPort with various Foundry states (will fail on unfixed code)

**Expected Counterexamples**:
- /foundry/stop endpoint returns 404
- Get-FoundryPort returns null even when Foundry is running
- /foundry/start returns success before service is actually ready

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode**:
```
FOR ALL input WHERE isBugCondition(input) DO
  result := fixedFunction(input)
  ASSERT expectedBehavior(result)
END FOR
```

**Test Cases**:
1. **Auto-start with Detection**: foundry_auto_start=true, verify service starts AND is detected
2. **UI Toggle Stop**: Call /foundry/stop, verify service stops AND UI updates
3. **UI Toggle Start**: Call /foundry/start, verify service starts AND port is returned
4. **Error Handling**: Call endpoints when Foundry CLI not found, verify proper error messages

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode**:
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalFunction(input) = fixedFunction(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for manual Foundry start, other AI backends, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Manual Start Preservation**: Foundry started manually, verify system detects it correctly
2. **Other Backends Preservation**: HuggingFace/llama.cpp/Ollama models work unchanged
3. **Config Loading Preservation**: config.json settings continue to work
4. **Environment Variables**: FOUNDRY_BASE_URL continues to be set correctly

### Unit Tests

- Test install.py /foundry/stop endpoint returns 200
- Test install.py /foundry/start endpoint returns port when service is ready
- Test Get-FoundryPort detects Foundry on correct port
- Test Get-FoundryPort returns null when Foundry not running
- Test error handling when Foundry CLI not found

### Property-Based Tests

- Generate random Foundry startup scenarios and verify detection works
- Generate random config.json settings and verify Foundry auto-start behavior
- Test that manual Foundry start continues to work across many scenarios
- Verify other AI backends remain unaffected by Foundry changes

### Integration Tests

- Test full start.ps1 flow with Foundry auto-start
- Test UI toggle switch start/stop cycle
- Test Foundry detection after manual service start
- Test error handling when Foundry CLI is missing
- Test port detection with multiple services running
