# Implementation Plan: OpenAI-Compatible /v1/models Endpoint

## Overview

This feature adds an OpenAI-compatible `/v1/models` endpoint to the FastAPI Foundry server. The endpoint aggregates models from all providers (Foundry, HuggingFace, llama.cpp, and Ollama) and maps provider-prefixed IDs to OpenAI-compatible format. The implementation follows the design document steps and includes property-based and unit tests.

## Tasks

- [ ] 1. Create new endpoint file `src/api/endpoints/openai_models.py`
  - [x] 1.1 Import necessary modules and configure logging
    - Import FastAPI, logging, asyncio, time, typing modules
    - Create router instance and logger
    - _Requirements: 1.1, 6.1_
  
  - [x] 1.2 Implement ID mapping function
    - Create `map_to_openai_id()` function to convert provider-prefixed IDs to OpenAI format
    - Replace `::` with `-` for provider prefixes
    - Pass through non-prefixed IDs unchanged
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [x] 1.3 Implement safe collection wrapper
    - Create `_safe_collect()` helper to handle provider collection errors
    - Log errors and return empty list on failure
    - _Requirements: 5.1, 5.3_
  
  - [x] 1.4 Implement provider model collection functions
    - `_collect_foundry()` - reuse existing `_collect_foundry()` from models.py
    - `_collect_hf()` - reuse existing `_collect_hf()` from models.py
    - `_collect_llama()` - reuse existing `_collect_llama()` from models.py
    - `_collect_ollama()` - reuse existing `_collect_ollama()` from models.py
    - _Requirements: 2.1, 2.2_
  
  - [x] 1.5 Implement model aggregation function
    - Create `collect_all_models()` using `asyncio.gather()`
    - Handle exceptions and continue with successful providers
    - Return unified list of all models
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [x] 1.6 Implement response builder function
    - Create `build_openai_response()` to transform internal models to OpenAI format
    - Map IDs using `map_to_openai_id()`
    - Build `data` array with `id`, `object`, `created`, `owned_by` fields
    - Calculate `total` count and `by_provider` breakdown
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 6.1, 6.2_
  
  - [ ] 1.7 Implement `/v1/models` endpoint
    - Create `@router.get("/v1/models")` endpoint
    - Call `collect_all_models()` and `build_openai_response()`
    - Return OpenAI-compatible response
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 6.1, 6.2_
  
  - [ ] 1.8 Add error handling
    - Wrap endpoint in try/except
    - Return empty response on error (HTTP 200)
    - Log errors with full context
    - _Requirements: 5.1, 5.2, 5.3_

- [ ]* 2. Write property-based tests for ID mapping
  - **Property 1: ID Mapping Preserves Provider Name**
  - **Validates: Requirements 3.1, 3.2, 3.3**
  - [ ] 2.1 Test `foundry::model-id` → `foundry-model-id`
  - [ ] 2.2 Test `hf::model-id` → `hf-model-id`
  - [ ] 2.3 Test `llama::path.gguf` → `llama-path.gguf`
  - [ ] 2.4 Test `ollama::model:tag` → `ollama-model:tag`
  - [ ] 2.5 Test non-prefixed ID passes through unchanged

- [ ]* 3. Write property-based tests for model aggregation
  - **Property 3: All Providers Are Aggregated**
  - **Validates: Requirements 2.1, 2.2**
  - [ ] 3.1 Test aggregation with models from all providers
  - [ ] 3.2 Test aggregation with empty provider lists
  - [ ] 3.3 Test aggregation with mixed empty/non-empty providers

- [ ]* 4. Write property-based tests for error handling
  - **Property 6: Error Logging and Continuation**
  - **Validates: Requirements 5.1**
  - [ ] 4.1 Test provider failure handling
  - [ ] 4.2 Test all providers fail scenario
  - [ ] 4.3 Test partial failure with some providers succeeding

- [ ]* 5. Write property-based tests for response structure
  - **Property 7: Response Structure Consistency**
  - **Validates: Requirements 1.2, 1.3, 6.1, 6.2**
  - [ ] 5.1 Test response contains required fields
  - [ ] 5.2 Test total matches data array length
  - [ ] 5.3 Test by_provider counts are accurate

- [ ]* 6. Write property-based tests for model object completeness
  - **Property 8: Model Object Completeness**
  - **Validates: Requirements 1.4, 1.5**
  - [ ] 6.1 Test model objects have all required fields
  - [ ] 6.2 Test object field is always "model"
  - [ ] 6.3 Test created field is Unix timestamp

- [ ] 7. Register new router in `src/api/app.py`
  - [x] 7.1 Add import for new router
    - Add `from .endpoints.openai_models import router as openai_models_router`
    - _Requirements: 1.1_
  
  - [x] 7.2 Include router at root level
    - Add `app.include_router(openai_models_router)` (no prefix)
    - _Requirements: 1.1_

- [ ]* 8. Write unit tests for edge cases
  - [ ] 8.1 Test empty model lists from all providers
  - [ ] 8.2 Test provider returning malformed data
  - [ ] 8.3 Test provider raising unexpected exception
  - [ ] 8.4 Test ID mapping with edge cases (multiple `::`, empty provider)

- [ ]* 9. Write integration tests
  - [ ] 9.1 Test full endpoint with mock providers
  - [ ] 9.2 Test with API key enabled
  - [ ] 9.3 Test CORS headers
  - [ ] 9.4 Test backward compatibility with `/api/v1/models`

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation reuses existing collection functions from `src/api/endpoints/models.py`
- The new endpoint coexists with `/api/v1/models` without interference (backward compatibility)