# Design Document: OpenAI-Compatible /v1/models Endpoint

## Overview

This feature adds an OpenAI-compatible `/v1/models` endpoint to the FastAPI Foundry server. The browser extension expects this endpoint to return models in the OpenAI API format, which differs from the current internal `/api/v1/models` endpoint format.

The new endpoint will:
- Aggregate models from all available providers (Foundry, HuggingFace, llama.cpp, and Ollama)
- Map provider-prefixed IDs (e.g., `foundry::model-id`) to OpenAI-compatible format (e.g., `foundry-model-id`)
- Return response in OpenAI format with `data` array containing `id` and `object` fields
- Include `total` field with model count
- Include optional `by_provider` field with provider breakdown
- Handle errors gracefully - continue if individual providers fail

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FastAPI Application                             │
│                              Port: 9696                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API Endpoints Layer                                  │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐  │
│  │ /api/v1/models       │  │ /v1/models (NEW)     │  │ /api/v1/...      │  │
│  │ (Existing, Internal) │  │ (New, OpenAI compat) │  │ (Other endpoints)│  │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────┘  │
│           │                         │                                        │
│           │                         ▼                                        │
│           │              ┌──────────────────────┐                            │
│           │              │  ID Mapper &         │                            │
│           │              │  Formatter           │                            │
│           │              │  - foundry:: → -     │                            │
│           │              │  - hf:: → -          │                            │
│           │              │  - llama:: → -       │                            │
│           │              │  - ollama:: → -      │                            │
│           │              └──────────────────────┘                            │
│           │                         │                                        │
│           │                         ▼                                        │
│           │              ┌──────────────────────┐                            │
│           │              │  Model Aggregator    │                            │
│           │              │  - Collect from all  │                            │
│           │              │    providers         │                            │
│           │              │  - Handle errors     │                            │
│           │              │  - Return unified    │                            │
│           │              └──────────────────────┘                            │
│           │                         │                                        │
│           ▼                         ▼                                        │
│  ┌──────────────────────┐  ┌──────────────────────┐                          │
│  │ Provider Collectors  │  │  Response Builder    │                          │
│  │ - Foundry models     │  │  - Build OpenAI      │                          │
│  │ - HuggingFace models │  │    format response   │                          │
│  │ - llama.cpp models   │  │  - Add metadata      │                          │
│  │ - Ollama models      │  │    (total, by_provider)│                        │
│  └──────────────────────┘  └──────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Endpoint Specification

### New Endpoint: GET /v1/models

**Location:** `src/api/endpoints/openai_models.py` (new file)

**Purpose:** Return models in OpenAI-compatible format for browser extension

**Request:**
```
GET /v1/models
Authorization: Bearer <api_key>  # if API_KEY is set
```

**Response (Success - 200 OK):**
```json
{
  "data": [
    {
      "id": "foundry-qwen3-0.6b-generic-cpu:4",
      "object": "model",
      "created": 1234567890,
      "owned_by": "foundry"
    },
    {
      "id": "hf-Qwen-Qwen2.5-0.5B-Instruct",
      "object": "model",
      "created": 1234567890,
      "owned_by": "huggingface"
    },
    {
      "id": "llama-gemma-4-E4B-it-Q4_K_M",
      "object": "model",
      "created": 1234567890,
      "owned_by": "llama.cpp"
    },
    {
      "id": "ollama-qwen2.5:0.5b",
      "object": "model",
      "created": 1234567890,
      "owned_by": "ollama"
    }
  ],
  "total": 4,
  "by_provider": {
    "foundry": 1,
    "huggingface": 1,
    "llama.cpp": 1,
    "ollama": 1
  }
}
```

**Response (Error - 500 Internal Server Error):**
```json
{
  "error": {
    "message": "Internal server error",
    "type": "server_error",
    "code": 500
  }
}
```

### ID Mapping Rules

| Input Format | Output Format | Example |
|-------------|---------------|---------|
| `foundry::model-id` | `foundry-model-id` | `foundry::qwen3-0.6b` → `foundry-qwen3-0.6b` |
| `hf::model-id` | `hf-model-id` | `hf::Qwen/Qwen2.5-0.5B` → `hf-Qwen/Qwen2.5-0.5B` |
| `llama::path.gguf` | `llama-path.gguf` | `llama::D:/models/gemma.gguf` → `llama-D:/models/gemma.gguf` |
| `ollama::model-name` | `ollama-model-name` | `ollama::qwen2.5:0.5b` → `ollama-qwen2.5:0.5b` |
| `model-id` (no prefix) | `model-id` | `custom-model` → `custom-model` |

### Response Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | array | Yes | Array of model objects |
| `total` | integer | Yes | Total number of models |
| `by_provider` | object | No | Object with provider names as keys and counts as values |

### Model Object Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | OpenAI-compatible model identifier |
| `object` | string | Yes | Always `"model"` |
| `created` | integer | Yes | Unix timestamp (placeholder: current time) |
| `owned_by` | string | Yes | Provider name (foundry, huggingface, llama.cpp, ollama) |

## Components and Interfaces

### New Files

1. **`src/api/endpoints/openai_models.py`** (NEW)
   - Contains the `/v1/models` endpoint
   - Implements ID mapping logic
   - Aggregates models from all providers
   - Builds OpenAI-compatible response

2. **`.kiro/specs/openai-compatible-api/.config.kiro`** (NEW)
   - Configuration file for the spec
   - Contains spec ID and workflow type

### Modified Files

1. **`src/api/app.py`**
   - Add import for new router
   - Include new router at root level (no prefix)

### Existing Files (No Changes)

- `src/api/endpoints/models.py` - Existing `/api/v1/models` endpoint remains unchanged
- `src/models/foundry_client.py` - Foundry client unchanged
- `src/models/hf_client.py` - HuggingFace client unchanged
- `src/models/llama_client.py` - llama.cpp client unchanged
- `src/models/ollama_client.py` - Ollama client unchanged

## Data Models

### OpenAI Model Object

```python
from pydantic import BaseModel
from typing import Optional, List, Dict

class OpenAIModel(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str
```

### OpenAI Response Object

```python
class OpenAIModelsResponse(BaseModel):
    data: List[OpenAIModel]
    total: int
    by_provider: Optional[Dict[str, int]] = None
```

### Provider Model Object (Internal)

```python
class ProviderModel(BaseModel):
    id: str  # Provider-prefixed (foundry::, hf::, etc.)
    name: str
    provider: str
    prefix: str
    loaded: bool
    cached: bool
    size: str
    device: str
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: ID Mapping Preserves Provider Name

*For any* provider-prefixed model ID (e.g., `provider::model-id`), the mapped OpenAI-compatible ID SHALL preserve the provider name as a prefix with hyphen separator (e.g., `provider-model-id`)

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 2: Non-Prefixed IDs Pass Through Unchanged

*For any* model ID that does not contain a provider prefix, the mapped ID SHALL be identical to the input

**Validates: Requirements 3.4**

### Property 3: All Providers Are Aggregated

*For any* set of models from all providers (Foundry, HuggingFace, llama.cpp, Ollama), the response SHALL include all models in the `data` array

**Validates: Requirements 2.1, 2.2**

### Property 4: Empty Provider Handling

*For any* subset of providers returning empty model lists, the response SHALL include models from non-empty providers

**Validates: Requirements 2.3**

### Property 5: All-Failures Edge Case

*For any* scenario where all providers return empty or fail, the response SHALL return an empty `data` array with HTTP 200

**Validates: Requirements 2.4, 5.3**

### Property 6: Error Logging and Continuation

*For any* provider that fails during model collection, the system SHALL log the error and continue processing other providers

**Validates: Requirements 5.1**

### Property 7: Response Structure Consistency

*For any* successful response, the JSON object SHALL contain a `data` array, a `total` integer, and an optional `by_provider` object

**Validates: Requirements 1.2, 1.3, 6.1, 6.2**

### Property 8: Model Object Completeness

*For any* model object in the `data` array, the object SHALL contain `id`, `object`, `created`, and `owned_by` fields

**Validates: Requirements 1.4, 1.5**

### Property 9: Backward Compatibility

*For any* request to `/api/v1/models`, the response SHALL maintain the existing format with `success`, `models`, `count`, and `by_provider` fields

**Validates: Requirements 4.1, 4.2, 4.3**

## Error Handling Strategy

### Error Categories

1. **Provider Collection Errors**
   - Log error with provider name
   - Continue with other providers
   - Include error indicator in model object if applicable

2. **Partial Failure Handling**
   - If some providers succeed, return their models
   - If all providers fail, return empty `data` array
   - Always return HTTP 200 for model listing (never 500)

3. **Mapping Errors**
   - Invalid provider prefixes should be caught during collection
   - Log unexpected prefix formats
   - Continue with valid models

### Error Response Format

```json
{
  "error": {
    "message": "Internal server error",
    "type": "server_error",
    "code": 500
  }
}
```

### Logging Strategy

- Log provider-specific errors with full context
- Log mapping failures with input ID
- Log aggregation summary (count per provider)
- Use structured logging for easier parsing

## Testing Strategy

### Dual Testing Approach

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs (when applicable)
- Together: Comprehensive coverage (unit tests catch concrete bugs, property tests verify general correctness)

### Property-Based Testing

**Library:** `fast-check` (JavaScript for browser extension tests) or `hypothesis` (Python for backend tests)

**Configuration:**
- Minimum 100 iterations per property test
- Tag format: `Feature: openai-compatible-api, Property {number}: {property_text}`

**Properties to Test:**

1. **Property 1: ID Mapping**
   - Generate random provider-prefixed IDs
   - Verify `::` is replaced with `-`
   - Verify provider name is preserved

2. **Property 2: Aggregation**
   - Generate random models from each provider
   - Verify all models appear in response
   - Verify counts match

3. **Property 3: Error Handling**
   - Simulate provider failures
   - Verify errors are logged
   - Verify other providers continue

4. **Property 4: Response Structure**
   - Generate random model lists
   - Verify all required fields present
   - Verify total matches data length

### Unit Tests

**Test Categories:**

1. **ID Mapping Tests**
   - Test `foundry::model-id` → `foundry-model-id`
   - Test `hf::Qwen/Qwen2.5` → `hf-Qwen/Qwen2.5`
   - Test `llama::path.gguf` → `llama-path.gguf`
   - Test `ollama::model:tag` → `ollama-model:tag`
   - Test non-prefixed ID passes through

2. **Aggregation Tests**
   - Test empty provider lists
   - Test mixed empty/non-empty providers
   - Test all providers return models

3. **Error Tests**
   - Test provider raises exception
   - Test provider returns empty
   - Test provider returns malformed data

4. **Integration Tests**
   - Test full endpoint with real providers
   - Test with API key enabled
   - Test CORS headers

### Test Tagging

Each property-based test MUST include a comment with the design property reference:

```python
# Feature: openai-compatible-api, Property 1: ID Mapping Preserves Provider Name
def test_id_mapping_preserves_provider():
    ...
```

## Implementation Steps

### Step 1: Create New Endpoint File

Create `src/api/endpoints/openai_models.py` with:

1. Import necessary modules
2. Define ID mapping function
3. Define model collection functions (reuse existing)
4. Define response builder function
5. Define `/v1/models` endpoint

### Step 2: Register New Router

Update `src/api/app.py`:

1. Import new router: `from .endpoints.openai_models import router as openai_models_router`
2. Include router at root level: `app.include_router(openai_models_router)`

### Step 3: Implement ID Mapping

Create a helper function:

```python
def map_to_openai_id(provider_prefixed_id: str) -> str:
    """Convert provider-prefixed ID to OpenAI-compatible format."""
    if "::" not in provider_prefixed_id:
        return provider_prefixed_id
    return provider_prefixed_id.replace("::", "-", 1)
```

### Step 4: Implement Model Aggregation

Reuse existing collection functions:

```python
async def collect_all_models() -> List[ProviderModel]:
    """Collect models from all providers."""
    results = await asyncio.gather(
        _collect_foundry(),
        _collect_hf(),
        _collect_llama(),
        _collect_ollama(),
        return_exceptions=True,
    )
    models = []
    for result in results:
        if isinstance(result, list):
            models.extend(result)
    return models
```

### Step 5: Build OpenAI Response

Transform internal models to OpenAI format:

```python
def build_openai_response(models: List[ProviderModel]) -> dict:
    """Build OpenAI-compatible response from internal models."""
    data = []
    by_provider = {}
    
    for model in models:
        openai_id = map_to_openai_id(model["id"])
        data.append({
            "id": openai_id,
            "object": "model",
            "created": int(time.time()),
            "owned_by": model["provider"]
        })
        provider = model["provider"]
        by_provider[provider] = by_provider.get(provider, 0) + 1
    
    return {
        "data": data,
        "total": len(data),
        "by_provider": by_provider
    }
```

### Step 6: Implement Endpoint

Create the `/v1/models` endpoint:

```python
@router.get("/v1/models")
async def get_openai_models():
    """Get models in OpenAI-compatible format."""
    try:
        models = await collect_all_models()
        response = build_openai_response(models)
        return response
    except Exception as e:
        logger.error("Error collecting models: %s", e)
        return {"data": [], "total": 0}
```

### Step 7: Add Error Handling

Wrap provider calls with error handling:

```python
async def _safe_collect(coro):
    """Execute collection coroutine and return empty list on failure."""
    try:
        return await coro
    except Exception as e:
        logger.error("Provider collection failed: %s", e)
        return []
```

### Step 8: Test Implementation

1. Run smoke test: `GET /v1/models` returns 200
2. Run property tests: 100 iterations for each property
3. Run unit tests: Verify edge cases
4. Run integration tests: Verify with real providers

## Response Format Examples

### Example 1: Normal Response

```json
{
  "data": [
    {
      "id": "foundry-qwen3-0.6b-generic-cpu:4",
      "object": "model",
      "created": 1704067200,
      "owned_by": "foundry"
    },
    {
      "id": "hf-Qwen-Qwen2.5-0.5B-Instruct",
      "object": "model",
      "created": 1704067200,
      "owned_by": "huggingface"
    }
  ],
  "total": 2,
  "by_provider": {
    "foundry": 1,
    "huggingface": 1
  }
}
```

### Example 2: Empty Response (All Providers Down)

```json
{
  "data": [],
  "total": 0,
  "by_provider": {}
}
```

### Example 3: Partial Response (Some Providers Down)

```json
{
  "data": [
    {
      "id": "foundry-qwen3-0.6b-generic-cpu:4",
      "object": "model",
      "created": 1704067200,
      "owned_by": "foundry"
    }
  ],
  "total": 1,
  "by_provider": {
    "foundry": 1
  }
}
```

### Example 4: Single Provider Response

```json
{
  "data": [
    {
      "id": "ollama-qwen2.5:0.5b",
      "object": "model",
      "created": 1704067200,
      "owned_by": "ollama"
    }
  ],
  "total": 1,
  "by_provider": {
    "ollama": 1
  }
}
```

## Backward Compatibility

The existing `/api/v1/models` endpoint remains unchanged and continues to return:

```json
{
  "success": true,
  "models": [...],
  "count": 4,
  "by_provider": {
    "foundry": 1,
    "huggingface": 1,
    "llama.cpp": 1,
    "ollama": 1
  }
}
```

Both endpoints coexist without interference.