# Requirements Document

## Introduction

This feature adds configuration control over automatic HuggingFace model loading at application startup. Currently, when the `foundry_ai.default_model` setting starts with "hf::", the HuggingFace model is automatically loaded into the FastAPI process memory. This behavior cannot be disabled, which may be undesirable for users who want to manage model loading manually or use alternative backends.

The feature introduces a new `huggingface.auto_load_default` boolean setting that allows users to disable automatic HuggingFace model loading while maintaining backward compatibility with the existing behavior.

## Glossary

- **System**: FastAPI Foundry - AI model orchestrator
- **HuggingFace Backend**: The system component that loads and manages HuggingFace Transformers models in process memory
- **HuggingFace Client**: The `hf_client` module that handles model loading and inference for HuggingFace models
- **Auto-Load**: The automatic loading of a model into memory during application startup
- **Default Model**: The model specified in `foundry_ai.default_model` that is automatically loaded if configured
- **Backend Prefix**: The prefix in a model identifier (e.g., "hf::", "foundry::") that determines which backend handles the model

## Requirements

### Requirement 1: HuggingFace Auto-Load Configuration

**User Story:** As a system administrator, I want to control whether HuggingFace models are automatically loaded at startup, so that I can manage resource usage and loading behavior.

#### Acceptance Criteria

1. WHERE `huggingface.auto_load_default` is true (default), THE System SHALL load the HuggingFace model specified in `foundry_ai.default_model` at startup
2. WHERE `huggingface.auto_load_default` is false, THE System SHALL skip loading the HuggingFace model at startup
3. WHERE `huggingface.auto_load_default` is not specified, THE System SHALL default to true (maintain current behavior)
4. THE System SHALL validate that `huggingface.auto_load_default` is a boolean value
5. IF `huggingface.auto_load_default` is not a boolean value, THEN THE System SHALL log an error and use the default value of true

### Requirement 2: Integration with Existing Auto-Load Logic

**User Story:** As a developer, I want the HuggingFace auto-load configuration to work alongside the existing Foundry auto-start settings, so that each backend can be controlled independently.

#### Acceptance Criteria

1. WHEN the application starts, THE System SHALL check `huggingface.auto_load_default` before attempting to load a HuggingFace model
2. WHEN `foundry_ai.auto_load_default` is false, THE System SHALL NOT load a Foundry model even if `huggingface.auto_load_default` is true
3. WHEN `huggingface.auto_load_default` is false, THE System SHALL NOT load a HuggingFace model even if `foundry_ai.auto_load_default` is true
4. THE HuggingFace auto-load check SHALL occur independently of the Foundry auto-load check

### Requirement 3: Configuration Persistence

**User Story:** As a user, I want the `huggingface.auto_load_default` setting to be persisted in config.json, so that my preference is maintained across application restarts.

#### Acceptance Criteria

1. WHEN `huggingface.auto_load_default` is set to a value, THE System SHALL save it to config.json
2. WHEN the application restarts, THE System SHALL read `huggingface.auto_load_default` from config.json
3. THE System SHALL preserve existing configuration values when adding the new setting

### Requirement 4: Logging and Diagnostics

**User Story:** As a system administrator, I want clear logging about HuggingFace model loading decisions, so that I can verify the configuration is working as expected.

#### Acceptance Criteria

1. WHEN `huggingface.auto_load_default` is true and a HuggingFace model is loaded, THE System SHALL log "Auto-loading HF default model: {model_id}"
2. WHEN `huggingface.auto_load_default` is false and a HuggingFace model would have been loaded, THE System SHALL log "Skipping HF model auto-load (auto_load_default is false)"
3. WHEN `huggingface.auto_load_default` is not specified, THE System SHALL use the default value of true and log the decision
4. IF HuggingFace model loading fails, THE System SHALL log the error with details

### Requirement 5: Backward Compatibility

**User Story:** As a user with existing deployments, I want the default behavior to remain unchanged, so that my existing deployments continue to work without modification.

#### Acceptance Criteria

1. WHERE `huggingface.auto_load_default` is not present in config.json, THE System SHALL behave as it does currently (auto-load if default_model starts with "hf::")
2. WHERE `huggingface.auto_load_default` is true, THE System SHALL behave identically to the current implementation
3. THE System SHALL NOT modify existing config.json files automatically

## Non-Functional Requirements

### Performance

- The auto-load configuration check SHALL add less than 1ms to application startup time
- The configuration read operation SHALL complete before any model loading attempts

### Reliability

- The System SHALL handle missing or invalid `huggingface.auto_load_default` values gracefully
- The System SHALL continue startup even if configuration parsing fails

### Maintainability

- The auto-load logic SHALL be clearly separated from the model loading implementation
- Configuration validation SHALL be centralized in the config module

## Edge Cases and Considerations

1. **Empty default_model**: If `foundry_ai.default_model` is empty or not set, no auto-load attempts shall be made regardless of `huggingface.auto_load_default` value

2. **Non-HF model prefix**: If `foundry_ai.default_model` starts with "foundry::", "llama::", "ollama::", or "lmstudio::", the `huggingface.auto_load_default` setting shall have no effect

3. **Concurrent backends**: If multiple backends are configured, each shall be controlled by its respective auto-load setting independently

4. **Configuration validation**: Invalid values (non-boolean) for `huggingface.auto_load_default` shall be rejected with a clear error message

5. **Environment override**: The setting shall be configurable via environment variable following the existing pattern (e.g., `HF_AUTO_LOAD_DEFAULT`)

## Future Considerations

1. Consider adding per-backend auto-start settings for other backends (llama.cpp, Ollama, LM Studio)

2. Consider adding a "manual" mode that loads models only when first requested

3. Consider adding metrics about auto-load success/failure rates