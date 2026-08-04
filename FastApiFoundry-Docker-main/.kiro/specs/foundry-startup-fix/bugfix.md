# Bugfix Requirements Document

## Introduction

This bugfix addresses critical startup and control issues with the Foundry Local AI service integration in AI Assistant (FastApiFoundry-Docker) version 0.7.1. The user reports two main problems:

1. **Startup Detection Failure**: Foundry doesn't start automatically when running `start.ps1`, with logs showing "Foundry не обнаружен" (Foundry not found) and "Foundry недоступен - функции ИИ будут отключены" (Foundry unavailable - AI features disabled)

2. **UI Toggle Switch Failure**: The UI toggle switch in the Foundry tab doesn't work - clicking it doesn't change state

Investigation revealed:
- The frontend JavaScript calls `/foundry/stop` endpoint but this endpoint doesn't exist in the backend
- The `/foundry/start` endpoint exists but may not be working correctly
- The `Get-FoundryPort` function in start.ps1 may have issues detecting the Foundry service

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN `start.ps1` is executed AND Foundry is not already running AND `foundry_auto_start=true` in config.json THEN the system displays "Foundry не обнаружен" and "Foundry недоступен - функции ИИ будут отключены" instead of starting Foundry

1.2 WHEN the user clicks the Foundry toggle switch in the UI to stop the service THEN the system makes a request to `/foundry/stop` endpoint which doesn't exist, causing a 404 error and the toggle state remains unchanged

1.3 WHEN the user clicks the Foundry toggle switch in the UI to start the service AND the `/foundry/start` endpoint fails to properly start the Foundry service OR the startup detection in `start.ps1` cannot find the running Foundry service THEN the system reports failure and AI features remain disabled

### Expected Behavior (Correct)

2.1 WHEN `start.ps1` is executed AND Foundry is not already running AND `foundry_auto_start=true` in config.json THEN the system SHALL start the Foundry service using `foundry service start` command AND detect the running service on the correct port AND set `FOUNDRY_BASE_URL` environment variable

2.2 WHEN the user clicks the Foundry toggle switch in the UI to stop the service THEN the system SHALL call the `/foundry/stop` endpoint which SHALL stop the Foundry service using `foundry service stop` command AND update the UI to reflect the stopped state

2.3 WHEN the user clicks the Foundry toggle switch in the UI to start the service THEN the system SHALL call the `/foundry/start` endpoint which SHALL start the Foundry service using `foundry service start` command AND update the UI to reflect the started state

### Unchanged Behavior (Regression Prevention)

3.1 WHEN Foundry is already running on a detected port THEN the system SHALL CONTINUE TO skip the auto-start process and use the existing running service

3.2 WHEN `foundry_auto_start=false` in config.json THEN the system SHALL CONTINUE TO skip automatic Foundry startup and proceed without Foundry support

3.3 WHEN the user manually starts Foundry using `foundry service start` outside the application THEN the system SHALL CONTINUE TO detect the running service and connect to it

3.4 WHEN Foundry models are loaded and the service is stopped THEN the system SHALL CONTINUE TO properly unload models and clean up resources
