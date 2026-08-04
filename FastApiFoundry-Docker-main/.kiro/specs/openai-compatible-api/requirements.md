# Requirements Document

## Introduction

This feature adds an OpenAI-compatible `/v1/models` endpoint to the FastAPI Foundry server. The browser extension expects this endpoint to return models in the OpenAI API format, which differs from the current internal `/api/v1/models` endpoint format. The new endpoint will aggregate models from all available providers (Foundry, HuggingFace, llama.cpp, and Ollama) and map provider-prefixed IDs to OpenAI-compatible format.

## Glossary

- **FastAPI Foundry**: The main application server providing unified access to local AI models
- **OpenAI API**: The standard API format used by OpenAI's models endpoint, with `data` array containing model objects with `id` and `object` fields
- **Foundry**: Microsoft Foundry Local, the ONNX-based AI model provider
- **HuggingFace (HF)**: HuggingFace Transformers, the PyTorch-based AI model provider
- **llama.cpp**: The CPU-based GGUF model provider
- **Ollama**: The local service-based AI model provider
- **Model Provider**: An AI model backend that supplies models to the system
- **Model ID**: A unique identifier for a model, currently prefixed by provider (e.g., `foundry::model-id`)

## Requirements

### Requirement 1: OpenAI-Compatible Endpoint

**User Story:** As a browser extension developer, I want to call `/v1/models` and receive models in OpenAI format, so that the extension can display available models without custom parsing.

#### Acceptance Criteria

1. WHEN a GET request is made to `/v1/models`, THE Server SHALL return a 200 OK response
2. THE Response SHALL contain a JSON object with a `data` field
3. THE `data` field SHALL be an array of model objects
4. EACH model object SHALL contain an `id` field with the model identifier
5. EACH model object SHALL contain an `object` field with value `"model"`
6. IF an error occurs, THEN THE Server SHALL return an appropriate HTTP error status code

### Requirement 2: Model Aggregation

**User Story:** As a user, I want to see all available models from all providers in one list, so that I can easily see what models are available for use.

#### Acceptance Criteria

1. WHEN models are available from multiple providers, THE Server SHALL include all models in the response
2. THE Server SHALL aggregate models from Foundry, HuggingFace, llama.cpp, and Ollama providers
3. IF a provider has no models available, THE Server SHALL continue to return models from other providers
4. IF all providers are unavailable, THE Server SHALL return an empty `data` array

### Requirement 3: ID Mapping

**User Story:** As a developer, I want model IDs to be in OpenAI-compatible format, so that the browser extension can process them without special handling.

#### Acceptance Criteria

1. WHEN a model ID contains a provider prefix (e.g., `foundry::model-id`), THE Server SHALL map it to OpenAI-compatible format
2. THE Mapped ID SHALL remove the provider prefix separator (`::`) and replace it with a hyphen (`-`)
3. THE Mapped ID SHALL preserve the provider name as a prefix (e.g., `foundry-model-id`)
4. IF a model ID already follows OpenAI format, THE Server SHALL return it unchanged

### Requirement 4: Backward Compatibility

**User Story:** As a developer, I want the existing `/api/v1/models` endpoint to continue working, so that internal tools and documentation remain valid.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/v1/models`, THE Server SHALL continue to return the existing format
2. THE Existing format SHALL include `success`, `models`, `count`, and `by_provider` fields
3. THE New `/v1/models` endpoint SHALL NOT affect the behavior of `/api/v1/models`

### Requirement 5: Error Handling

**User Story:** As a user, I want to see available models even if some providers fail, so that I can still use working models.

#### Acceptance Criteria

1. WHEN a provider is unavailable, THE Server SHALL log the error and continue processing other providers
2. IF a provider returns an error, THE Server SHALL include an error indicator in the model object
3. WHEN all providers are unavailable, THE Server SHALL return an empty `data` array with HTTP 200

### Requirement 6: Response Metadata

**User Story:** As a developer, I want to know how many models are available, so that I can display a count to users.

#### Acceptance Criteria

1. THE Response SHALL include a `total` field with the total number of models
2. THE Response MAY include a `by_provider` field with model counts per provider
3. IF provider counts are unavailable, THE `by_provider` field MAY be omitted
