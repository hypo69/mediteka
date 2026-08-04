# Implementation Plan

- [ ] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Foundry Startup and UI Toggle Failures
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: For deterministic bugs, scope the property to the concrete failing case(s) to ensure reproducibility
  - Test implementation details from Bug Condition in design
  - The test assertions should match the Expected Behavior Properties from design
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Existing Foundry and AI Backend Functionality
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 3. Fix for Foundry startup detection and UI toggle switch failures

  - [x] 3.1 Add /foundry/stop endpoint to install.py
    - Add POST endpoint `/install/foundry/stop` that calls `foundry service stop`
    - Return appropriate success/error response matching foundry_management.py format
    - _Bug_Condition: isBugCondition(input) where input.ui_action = "toggle_click" AND input.endpoint_missing = true_
    - _Expected_Behavior: stop_foundry() returns {"success": True} and stops Foundry service_
    - _Preservation: Manual Foundry service management continues to work unchanged_
    - _Requirements: 1.2, 2.2, 3.2_

  - [x] 3.2 Improve /foundry/start endpoint in install.py with readiness detection
    - Add service readiness detection after starting Foundry service
    - Poll for service availability using same logic as Get-FoundryPort
    - Return port information in response for UI to update FOUNDRY_BASE_URL
    - _Bug_Condition: isBugCondition(input) where input.service_started = true AND input.port_detection = false_
    - _Expected_Behavior: start_foundry() waits for service ready and returns {"success": True, "port": <port>, "url": "<url>"}_
    - _Preservation: Manual Foundry start continues to work unchanged_
    - _Requirements: 1.3, 2.1, 3.1_

  - [x] 3.3 Improve Get-FoundryPort function in start.ps1
    - Add fallback detection using netstat to find Foundry process
    - Verify process name pattern matches "Inference.Service.Agent" correctly
    - Add additional health check endpoint verification for /v1/models
    - Handle cases where multiple ports are listening
    - Add timeout handling for health checks
    - _Bug_Condition: isBugCondition(input) where input.port_detection = false but Foundry is running_
    - _Expected_Behavior: Get-FoundryPort returns correct port when Foundry is running_
    - _Preservation: Manual Foundry detection continues to work unchanged_
    - _Requirements: 1.1, 2.1, 3.1, 3.3_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Foundry Startup and UI Toggle Failures
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Existing Foundry and AI Backend Functionality
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
