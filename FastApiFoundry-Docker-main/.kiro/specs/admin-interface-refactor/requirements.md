# Requirements Document

## Introduction

This document specifies requirements for refactoring the admin interface in the AI Assistant project. The current interface serves as the main administration panel at the root URL (`/`) and uses a tabbed SPA architecture with partials. The refactoring will restructure URLs, remove hardcoded configuration, and improve maintainability while preserving all existing functionality.

## Glossary

- **Admin Interface**: The main web interface served at `/static/interface/` providing model management, configuration, and monitoring
- **Foundry**: Microsoft Foundry Local - ONNX-based AI model runtime
- **HuggingFace (HF)**: HuggingFace Transformers - PyTorch-based AI model runtime
- **llama.cpp**: CPU-based AI model runtime using GGUF format
- **Ollama**: Local AI model service
- **RAG**: Retrieval-Augmented Generation system for knowledge retrieval
- **MCP**: Model Context Protocol servers
- **SPA**: Single Page Application architecture
- **i18n**: Internationalization/localization system
- **API Endpoint**: REST API endpoint under `/api/v1/` prefix
- **Model Prefix**: Identifier prefix used to route requests to specific backends (e.g., `foundry::model-id`)

## Requirements

### Requirement 1: Remove Hardcoded Models Configuration

**User Story:** As an administrator, I want the interface to fetch available models from the API instead of using a hardcoded JSON file, so that the interface always displays current model availability.

#### Acceptance Criteria

1. WHEN the models tab is loaded, THE Interface SHALL fetch model data from `/api/v1/models` endpoint instead of reading `static/available_models.json`
2. WHILE the interface is running, THE Interface SHALL automatically refresh model data when models are loaded or unloaded
3. IF the API endpoint `/api/v1/models` is unavailable, THEN THE Interface SHALL display an error message and continue operating in degraded mode
4. WHERE model data is fetched from the API, THE Interface SHALL cache the data locally for offline viewing during the session

### Requirement 2: Restructure URL Navigation

**User Story:** As a user, I want the admin interface to be accessible at `/admin` instead of the root URL, so that different interface sections have clear, organized URLs.

#### Acceptance Criteria

1. WHEN a user navigates to `/admin`, THE Application SHALL load the admin interface with all tabs functional
2. WHEN a user navigates to `/install`, THE Application SHALL load the GUI installer SPA from `static/gui-install/`
3. WHEN a user navigates to `/agents/<agent-name>`, THE Application SHALL load the agent management page for the specified agent
4. WHERE a user is currently at the root URL (`/`), THE Application SHALL automatically redirect to `/admin`
5. IF the requested agent name is invalid or inaccessible, THEN THE Application SHALL display an error page with navigation options

### Requirement 3: Maintain Existing SPA Architecture

**User Story:** As a developer, I want to preserve the existing SPA architecture with tabs and partials, so that the interface remains maintainable and follows established patterns.

#### Acceptance Criteria

1. THE Interface SHALL continue to use Bootstrap 5 for UI components
2. THE Interface SHALL continue to use i18next for internationalization
3. THE Interface SHALL continue to use modular JavaScript in `static/interface/js/`
4. WHILE navigating between tabs, THE Interface SHALL not reload the page or reinitialize modules unnecessarily
5. WHERE tab navigation occurs, THE Interface SHALL preserve the active tab state in the URL hash or history

### Requirement 4: Preserve All Existing Functionality

**User Story:** As an administrator, I want all existing interface functionality to continue working after the refactoring, so that I can manage models, configuration, and monitoring without disruption.

#### Acceptance Criteria

1. THE Interface SHALL provide all current tabs: Models, Foundry, HuggingFace, llama.cpp, RAG, Chat, Settings, Editor, MCP Servers, Agent, API Keys, Logs, and API Documentation
2. WHEN a model is loaded or unloaded, THE Interface SHALL update the active model status and available model lists
3. WHILE editing configuration, THE Interface SHALL validate changes before saving and provide rollback options
4. IF an API call fails, THEN THE Interface SHALL display appropriate error messages and allow retry
5. WHERE settings are modified, THE Interface SHALL persist changes to `config.json` and apply them on next restart

### Requirement 5: Maintain Backward Compatibility

**User Story:** As an administrator, I want existing bookmarks and links to continue working, so that users don't experience broken navigation.

#### Acceptance Criteria

1. WHERE a user visits `/` (root URL), THE Application SHALL redirect to `/admin` with a 302 status code
2. THE Interface SHALL continue to support direct navigation to specific tabs via URL parameters (e.g., `/#models`, `/#chat`)
3. IF legacy URLs or bookmarks reference the old interface structure, THE Application SHALL handle them gracefully with appropriate redirects
4. WHERE API endpoints are used by the interface, THE Application SHALL maintain the same endpoint signatures and response formats
5. WHEN the interface loads, THE Application SHALL check for deprecated configuration keys and migrate them automatically

### Requirement 6: API Endpoint Dependencies

**User Story:** As a developer, I want to clearly document all API endpoints used by the interface, so that backend changes can be coordinated with frontend updates.

#### Acceptance Criteria

1. THE Interface SHALL use the following API endpoints:
   - `GET /api/v1/health` - Service health status
   - `GET /api/v1/models` - All available models
   - `GET /api/v1/foundry/models/loaded` - Foundry models in memory
   - `GET /api/v1/foundry/models/cached` - Foundry models on disk
   - `GET /api/v1/hf/models` - HuggingFace models (loaded + downloaded)
   - `GET /api/v1/llama/status` - llama.cpp server status
   - `GET /api/v1/llama/models` - llama.cpp available models
   - `GET /api/v1/ollama/models` - Ollama local models
   - `GET /api/v1/rag/status` - RAG system status
   - `GET /api/v1/config` - Current configuration
   - `PATCH /api/v1/config` - Update configuration
   - `GET /api/v1/system/stats` - System resource usage
2. WHEN any API endpoint returns an error, THE Interface SHALL handle it gracefully with appropriate user feedback
3. WHERE rate limiting is applicable, THE Interface SHALL implement debouncing to avoid excessive API calls
4. THE Interface SHALL include error handling for network failures, timeouts, and invalid responses

### Requirement 7: Performance Requirements

**User Story:** As a user, I want the interface to load and respond quickly, so that my workflow is not interrupted by slow operations.

#### Acceptance Criteria

1. WHEN the interface loads, THE Page SHALL be fully interactive within 2 seconds on a standard connection
2. WHILE fetching model data, THE Interface SHALL display a loading indicator and update incrementally as data arrives
3. IF a tab contains heavy operations (e.g., RAG index building), THE Interface SHALL provide progress feedback and allow cancellation
4. WHERE model lists are displayed, THE Interface SHALL implement virtual scrolling or pagination for lists exceeding 100 items
5. THE Interface SHALL cache static assets (CSS, JS, partials) with appropriate cache headers

### Requirement 8: Maintainability Requirements

**User Story:** As a developer, I want the interface code to be well-organized and documented, so that future enhancements are straightforward.

#### Acceptance Criteria

1. THE Interface SHALL maintain the existing modular JavaScript structure with separate files per feature
2. WHERE new features are added, THE Code SHALL follow the existing patterns and conventions
3. THE Codebase SHALL include JSDoc comments for all public functions and modules
4. IF configuration changes are made, THE Interface SHALL log the changes with timestamps and user context
5. WHERE error conditions occur, THE Interface SHALL provide detailed error messages for debugging

### Requirement 9: Security Requirements

**User Story:** As an administrator, I want the interface to protect sensitive operations, so that unauthorized changes cannot be made.

#### Acceptance Criteria

1. WHERE configuration changes are made, THE Interface SHALL require confirmation for destructive operations
2. THE Interface SHALL validate all user inputs before sending to API endpoints
3. IF an API call requires authentication, THE Interface SHALL handle authentication tokens securely
4. WHERE sensitive data is displayed (e.g., API keys), THE Interface SHALL mask the data and require explicit action to reveal
5. THE Interface SHALL prevent cross-site scripting (XSS) by properly escaping all dynamic content

### Requirement 10: Localization Support

**User Story:** As a multilingual user, I want the interface to support multiple languages, so that I can use it in my preferred language.

#### Acceptance Criteria

1. THE Interface SHALL continue to support Russian and English languages via i18next
2. WHEN a language is selected, THE Interface SHALL apply the selection to all UI elements
3. WHERE new text is added to the interface, THE Interface SHALL include translation keys for all supported languages
4. THE Interface SHALL persist the user's language preference in local storage
5. IF a translation is missing, THE Interface SHALL fall back to English and log the missing key
