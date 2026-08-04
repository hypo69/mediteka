/**
 * =============================================================================
 * Process Name: Unified LLM Providers Registry
 * =============================================================================
 * Description:
 *   Single source of truth for provider metadata and model-fetching logic.
 *   Used by BOTH the FastAPI Foundry web app (static/js/) and the browser
 *   extension (extensions/browser-extension-summarizer/).
 *
 *   Each provider entry:
 *     label          — human-readable name for UI
 *     placeholder    — API key input hint
 *     hint           — URL where the key can be obtained (without https://)
 *     fetchModels    — async (apiKey, opts?) => [{id, label}]
 *                      opts.customUrl — used only by 'custom' provider
 *
 * Storage contract (NOT handled here):
 *   Web app  → keys stored in .env via /api/v1/config/provider-keys
 *   Extension → keys stored in chrome.storage.sync as arrays
 *   Both sides use the shared export/import file format (see EXPORT_FORMAT below).
 *
 * Export/Import file format (version 2):
 *   {
 *     schema:         "ai-assistant-config",   // identifies the file type
 *     version:        2,
 *     exportedAt:     ISO8601 string,
 *     exportedFrom:   "app" | "extension",
 *     providerKeys:   { [providerId]: string | string[] },
 *     customModels:   { [providerId]: [{id, label}] },   // optional
 *     activeProvider: string | null,
 *     activeModel:    string | null,
 *     // Extension-only fields (ignored by app on import):
 *     activeKeyIndex: { [providerId]: number },
 *     providerModels: { [providerId]: [{id, label}] },
 *     summaryLang:    string,
 *     summaryProvider: string,
 *     summaryModel:   string,
 *   }
 *
 * File: providers-registry.js
 * Project: FastApiFoundry (Docker)
 * Version: 0.6.0
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

export const PROVIDERS = {

    // ── Google Gemini ────────────────────────────────────────────────────────
    // Key passed as ?key= query param (not Bearer) — Gemini-specific.
    // Filter to generateContent-capable models only.
    gemini: {
        label: 'Google Gemini',
        placeholder: 'AIza…',
        hint: 'aistudio.google.com/app/apikey',
        fetchModels: async (apiKey) => {
            const r = await fetch(
                `https://generativelanguage.googleapis.com/v1/models?key=${encodeURIComponent(apiKey)}`
            );
            const d = await r.json();
            if (!r.ok) throw new Error(d.error?.message || `HTTP ${r.status}`);
            return (d.models || [])
                .filter(m => m.supportedGenerationMethods?.includes('generateContent'))
                .map(m => ({ id: m.name.replace('models/', ''), label: m.displayName || m.name }));
        }
    },

    // ── OpenAI ───────────────────────────────────────────────────────────────
    // Filter to chat models only (gpt-*, o1-*, o3-*), sorted newest first.
    openai: {
        label: 'OpenAI',
        placeholder: 'sk-…',
        hint: 'platform.openai.com/api-keys',
        fetchModels: async (apiKey) => {
            const r = await fetch('https://api.openai.com/v1/models', {
                headers: { Authorization: `Bearer ${apiKey}` }
            });
            const d = await r.json();
            if (!r.ok) throw new Error(d.error?.message || `HTTP ${r.status}`);
            return (d.data || [])
                .filter(m => /^(gpt|o1|o3)/.test(m.id))
                .sort((a, b) => b.created - a.created)
                .map(m => ({ id: m.id, label: m.id }));
        }
    },

    // ── OpenRouter ───────────────────────────────────────────────────────────
    openrouter: {
        label: 'OpenRouter',
        placeholder: 'sk-or-…',
        hint: 'openrouter.ai/keys',
        fetchModels: async (apiKey) => {
            const r = await fetch('https://openrouter.ai/api/v1/models', {
                headers: { Authorization: `Bearer ${apiKey}` }
            });
            const d = await r.json();
            if (!r.ok) throw new Error(d.error?.message || `HTTP ${r.status}`);
            return (d.data || []).map(m => ({ id: m.id, label: m.name || m.id }));
        }
    },

    // ── Anthropic Claude ─────────────────────────────────────────────────────
    // Uses x-api-key header + anthropic-version (not Bearer).
    anthropic: {
        label: 'Anthropic Claude',
        placeholder: 'sk-ant-…',
        hint: 'console.anthropic.com/settings/keys',
        fetchModels: async (apiKey) => {
            const r = await fetch('https://api.anthropic.com/v1/models', {
                headers: { 'x-api-key': apiKey, 'anthropic-version': '2023-06-01' }
            });
            const d = await r.json();
            if (!r.ok) throw new Error(d.error?.message || `HTTP ${r.status}`);
            return (d.data || []).map(m => ({ id: m.id, label: m.display_name || m.id }));
        }
    },

    // ── Mistral AI ───────────────────────────────────────────────────────────
    // Filter to chat-capable models only.
    mistral: {
        label: 'Mistral AI',
        placeholder: '…',
        hint: 'console.mistral.ai/api-keys',
        fetchModels: async (apiKey) => {
            const r = await fetch('https://api.mistral.ai/v1/models', {
                headers: { Authorization: `Bearer ${apiKey}` }
            });
            const d = await r.json();
            if (!r.ok) throw new Error(d.error?.message || d.message || `HTTP ${r.status}`);
            return (d.data || [])
                .filter(m => m.capabilities?.completion_chat)
                .sort((a, b) => b.created - a.created)
                .map(m => ({ id: m.id, label: m.name || m.id }));
        }
    },

    // ── Groq ─────────────────────────────────────────────────────────────────
    groq: {
        label: 'Groq',
        placeholder: 'gsk_…',
        hint: 'console.groq.com/keys',
        fetchModels: async (apiKey) => {
            const r = await fetch('https://api.groq.com/openai/v1/models', {
                headers: { Authorization: `Bearer ${apiKey}` }
            });
            const d = await r.json();
            if (!r.ok) throw new Error(d.error?.message || `HTTP ${r.status}`);
            return (d.data || [])
                .filter(m => m.active !== false)
                .sort((a, b) => b.created - a.created)
                .map(m => ({ id: m.id, label: m.id }));
        }
    },

    // ── Cohere ───────────────────────────────────────────────────────────────
    // v2 API — errors in .message, not .error.
    cohere: {
        label: 'Cohere',
        placeholder: '…',
        hint: 'dashboard.cohere.com/api-keys',
        fetchModels: async (apiKey) => {
            const r = await fetch(
                'https://api.cohere.com/v2/models?default_only=false&endpoint=chat&page_size=50',
                { headers: { Authorization: `Bearer ${apiKey}` } }
            );
            const d = await r.json();
            if (!r.ok) throw new Error(d.message || `HTTP ${r.status}`);
            return (d.models || []).map(m => ({ id: m.name, label: m.name }));
        }
    },

    // ── DeepSeek ─────────────────────────────────────────────────────────────
    deepseek: {
        label: 'DeepSeek',
        placeholder: 'sk-…',
        hint: 'platform.deepseek.com/api_keys',
        fetchModels: async (apiKey) => {
            const r = await fetch('https://api.deepseek.com/models', {
                headers: { Authorization: `Bearer ${apiKey}` }
            });
            const d = await r.json();
            if (!r.ok) throw new Error(d.error?.message || `HTTP ${r.status}`);
            return (d.data || []).map(m => ({ id: m.id, label: m.id }));
        }
    },

    // ── xAI Grok ─────────────────────────────────────────────────────────────
    xai: {
        label: 'xAI Grok',
        placeholder: 'xai-…',
        hint: 'console.x.ai',
        fetchModels: async (apiKey) => {
            const r = await fetch('https://api.x.ai/v1/models', {
                headers: { Authorization: `Bearer ${apiKey}` }
            });
            const d = await r.json();
            if (!r.ok) throw new Error(d.error?.message || `HTTP ${r.status}`);
            return (d.data || []).map(m => ({ id: m.id, label: m.id }));
        }
    },

    // ── NVIDIA NIM ───────────────────────────────────────────────────────────
    nvidia: {
        label: 'NVIDIA NIM',
        placeholder: 'nvapi-…',
        hint: 'build.nvidia.com',
        fetchModels: async (apiKey) => {
            const r = await fetch('https://integrate.api.nvidia.com/v1/models', {
                headers: { Authorization: `Bearer ${apiKey}` }
            });
            const d = await r.json();
            if (!r.ok) throw new Error(d.error?.message || JSON.stringify(d.error) || `HTTP ${r.status}`);
            return (d.data || []).map(m => ({ id: m.id, label: m.id }));
        }
    },

    // ── HuggingFace ──────────────────────────────────────────────────────────
    // Token stored as HF_TOKEN in .env. Uses /api/v1/config/env endpoint.
    // fetchModels lists downloaded local models via the app's own HF API.
    huggingface: {
        label: 'HuggingFace',
        placeholder: 'hf_…',
        hint: 'huggingface.co/settings/tokens',
        fetchModels: async () => {
            const r = await fetch('/api/v1/hf/models');
            const d = await r.json();
            if (!r.ok) throw new Error(d.error || `HTTP ${r.status}`);
            return (d.downloaded || []).map(m => ({ id: m.id, label: m.id }));
        }
    },

    // ── Custom (OpenAI-compatible) ───────────────────────────────────────────
    // For self-hosted: Ollama, LM Studio, vLLM, FastAPI Foundry.
    // opts.customUrl — base URL, e.g. http://localhost:9696/v1
    custom: {
        label: 'Custom (OpenAI-compatible)',
        placeholder: 'API key…',
        hint: '',
        fetchModels: async (apiKey, opts = {}) => {
            const base = (opts.customUrl || 'http://localhost:9696/v1').replace(/\/$/, '');
            const headers = apiKey ? { Authorization: `Bearer ${apiKey}` } : {};
            const r = await fetch(`${base}/models`, { headers });
            const d = await r.json();
            if (!r.ok) throw new Error(d.error?.message || `HTTP ${r.status}`);
            return (d.data || []).map(m => ({ id: m.id, label: m.id }));
        }
    }
};

// ── Shared export file format ────────────────────────────────────────────────

/** Current schema version for the shared export/import file. */
export const CONFIG_SCHEMA_VERSION = 2;
export const CONFIG_SCHEMA_NAME    = 'ai-assistant-config';

/**
 * Validates that a parsed JSON object is a recognized config file.
 * Returns null if valid, or an error string if not.
 *
 * @param {object} obj
 * @returns {string|null}
 */
export function validateConfigFile(obj) {
    if (!obj || typeof obj !== 'object')          return 'Not an object';
    if (obj.schema !== CONFIG_SCHEMA_NAME)        return `Unknown schema: ${obj.schema}`;
    if (obj.version !== 1 && obj.version !== 2)  return `Unsupported version: ${obj.version}`;
    if (typeof obj.providerKeys !== 'object')     return 'Missing providerKeys';
    return null;
}

/**
 * Normalizes providerKeys to always be { [id]: string } (first key wins for arrays).
 * The app stores single strings; the extension stores arrays.
 *
 * @param {object} providerKeys  raw providerKeys from the file
 * @returns {{ [id]: string }}
 */
export function normalizeProviderKeys(providerKeys) {
    const out = {};
    for (const [id, val] of Object.entries(providerKeys || {})) {
        out[id] = Array.isArray(val) ? (val[0] || '') : String(val || '');
    }
    return out;
}

/**
 * Wraps providerKeys values as arrays (extension format).
 *
 * @param {object} providerKeys  { [id]: string }
 * @returns {{ [id]: string[] }}
 */
export function wrapProviderKeysAsArrays(providerKeys) {
    const out = {};
    for (const [id, val] of Object.entries(providerKeys || {})) {
        if (id === 'custom_url') { out[id] = val; continue; }
        out[id] = val ? [val] : [];
    }
    return out;
}
