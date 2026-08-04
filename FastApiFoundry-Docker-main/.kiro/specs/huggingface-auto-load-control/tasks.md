# Implementation Plan: HuggingFace Auto-Load Control

## Overview

This implementation adds configuration control over automatic HuggingFace model loading at application startup. The feature introduces a new `huggingface.auto_load_default` boolean setting that allows users to disable automatic HuggingFace model loading while maintaining backward compatibility.

The implementation follows a three-phase approach:
1. **Configuration**: Add the new property to config_manager.py with environment variable support
2. **Auto-Load Logic**: Modify lifespan() in src/api/app.py to check the new setting
3. **Testing**: Write comprehensive tests (property-based, unit, integration)

## Tasks

- [ ] 1. Add huggingface_auto_load_default property to Config class
  - [ ] 1.1 Add huggingface_auto_load_default property to config_manager.py
    - Implement property with environment variable priority (HF_AUTO_LOAD_DEFAULT)
    - Fall back to config.json value with default of True
    - Add validation for non-boolean values with error logging
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.3_
  
  - [ ]* 1.2 Write property test for huggingface_auto_load_default
    - **Property 3: Default value is true**
    - **Validates: Requirements 1.3, 5.1**
    - Test that default value is True when not specified
    - Test environment variable override with various formats ("true", "1", "yes")
    - _Test: Property 3_

  - [ ]* 1.3 Write unit tests for configuration edge cases
    - Test invalid config values (string, number, null)
    - Test environment variable parsing edge cases
    - Test fallback behavior when config.json is missing huggingface section
    - _Test: U3, U4, U5_

- [ ] 2. Modify lifespan() auto-load logic in src/api/app.py
  - [ ] 2.1 Add huggingface.auto_load_default check to lifespan()
    - Check `huggingface_auto_load_default` before loading HF model
    - Add logging for skip case when auto_load_default is false
    - Ensure independence from foundry_auto_load_default
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 4.1, 4.2, 4.3_
  
  - [ ]* 2.2 Write property test for auto-load behavior
    - **Property 1: Auto-load enabled loads HF model**
    - **Validates: Requirements 1.1, 5.1, 5.2**
    - Test that model loads when auto_load_default is True
    - Test that model does NOT load when auto_load_default is False
    - _Test: Property 1, Property 2_

  - [ ]* 2.3 Write unit tests for auto-load scenarios
    - Test empty default_model (no auto-load attempt)
    - Test non-HF prefixes (foundry::, llama::, etc.)
    - Test both backends disabled
    - Test both backends enabled
    - _Test: U1, U2, U6, U7_

- [ ] 3. Update configuration files
  - [ ] 3.1 Update config.json with new setting
    - Add `auto_load_default: true` to huggingface section
    - Preserve all existing configuration values
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 3.2 Update .env.example with HF_AUTO_LOAD_DEFAULT
    - Add environment variable example
    - Document the variable in comments
    - _Requirements: 5.3_

- [ ] 4. Add configuration validation function
  - [ ] 4.1 Implement validate_huggingface_auto_load_default()
    - Validate boolean type
    - Return error message for invalid values
    - Log validation errors
    - _Requirements: 1.4, 1.5_
  
  - [ ]* 4.2 Write unit tests for validation function
    - Test valid boolean values (True, False)
    - Test invalid values (string, number, null, list)
    - Test edge cases (empty string, None)
    - _Test: U3_

- [ ] 5. Integration tests
  - [ ]* 5.1 Write integration test for full startup with auto-load enabled
    - **Property 1: Auto-load enabled loads HF model**
    - Test complete startup flow with auto_load_default=true
    - Verify model loading logs
    - _Test: Property 1, I1_
  
  - [ ]* 5.2 Write integration test for full startup with auto-load disabled
    - **Property 2: Auto-load disabled skips HF model**
    - Test complete startup flow with auto_load_default=false
    - Verify skip logs
    - _Test: Property 2, I2_
  
  - [ ]* 5.3 Write integration test for environment variable override
    - **Property 8: Environment variable override**
    - Test HF_AUTO_LOAD_DEFAULT=false overrides config.json
    - Test HF_AUTO_LOAD_DEFAULT=true overrides config.json
    - _Test: Property 8, I4_

- [ ] 6. Checkpoint - Ensure all tests pass
  - Run full test suite
  - Verify all property tests pass (100+ iterations)
  - Verify all unit tests pass
  - Verify all integration tests pass
  - Ensure code coverage ≥ 90%
  - Ask the user if questions arise.

- [ ] 7. Documentation updates
  - [ ] 7.1 Update README.md with feature description
    - Document the new huggingface.auto_load_default setting
    - Explain environment variable support
    - Provide configuration examples
    - _Requirements: All_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation maintains backward compatibility by defaulting to `true`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "3.1", "4.1"] },
    { "id": 3, "tasks": ["3.2", "4.2", "5.1", "5.2"] },
    { "id": 4, "tasks": ["5.3", "6"] },
    { "id": 5, "tasks": ["7.1"] }
  ]
}
```
