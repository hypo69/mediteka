/**
 * config.js — Configuration management
 *
 * Handles loading, saving and exchanging settings via /api/v1/config.
 */

import { showAlert } from './ui.js';

// ── Load ──────────────────────────────────────────────────────────────────────

/**
 * Load main config from server and populate global window.CONFIG.
 * Returns the raw response data so app.js can read app.language.
 */
export async function loadConfig() {
    try {
        const response = await fetch(`${window.API_BASE}/config`);
        const data = await response.json();

        if (data.success) {
            window.CONFIG.foundry_url        = data.foundry_ai?.base_url || window.CONFIG.foundry_url;
            window.CONFIG.default_model      = data.foundry_ai?.default_model;
            window.CONFIG.auto_load_default  = data.foundry_ai?.auto_load_default || false;
            window.CONFIG.ollama_url         = data.config?.ollama?.base_url || data.ollama?.base_url || window.CONFIG.ollama_url || 'http://localhost:11434';
            window.CONFIG.ollama_temperature = data.config?.ollama?.temperature ?? data.ollama?.temperature ?? window.CONFIG.ollama_temperature ?? 0.7;
            window.CONFIG.ollama_top_p       = data.config?.ollama?.top_p ?? data.ollama?.top_p ?? window.CONFIG.ollama_top_p ?? 0.9;
            window.CONFIG.ollama_top_k       = data.config?.ollama?.top_k ?? data.ollama?.top_k ?? window.CONFIG.ollama_top_k ?? 50;
            window.CONFIG.ollama_max_tokens  = data.config?.ollama?.max_tokens ?? data.ollama?.max_tokens ?? window.CONFIG.ollama_max_tokens ?? 2048;

            // Restore chat settings from config.json
            if (window.applyChatConfig) window.applyChatConfig(data.foundry_ai);

            // Restore llama.cpp port
            const llamaPort = data.config?.llama_cpp?.port || 9780;
            const llamaPortEl = document.getElementById('llama-port');
            if (llamaPortEl) llamaPortEl.value = llamaPort;

            console.log('Config loaded');
        }
        
        // Update foundry_url from /health if base_url is empty
        if (!window.CONFIG.foundry_url) {
            try {
                const healthResponse = await fetch(`${window.API_BASE}/health`);
                const healthData = await healthResponse.json();
                if (healthData.foundry_status?.url) {
                    window.CONFIG.foundry_url = healthData.foundry_status.url;
                }
            } catch (e) {
                console.debug('Failed to get foundry_url from /health:', e);
            }
        }
        
        return data;
    } catch (error) {
        console.error('Failed to load config:', error);
        return null;
    }
}

// ── Load fields (Settings tab) ────────────────────────────────────────────────

/**
 * Fill Settings form fields with values from config.json.
 */
export async function loadConfigFields() {
    try {
        const response = await fetch(`${window.API_BASE}/config`);
        const data = await response.json();

        if (!data.success || !data.config) {
            showAlert('Failed to load config fields', 'danger');
            return;
        }

        const { fastapi_server, foundry_ai, docs_server, llama_cpp } = data.config;
        const dirs = data.config?.directories || {};

        const set = (id, val) => { const el = document.getElementById(id); if (el) el.value = val; };
        const chk = (id, val) => { const el = document.getElementById(id); if (el) el.checked = !!val; };

        // Ports
        set('config-api-port',  fastapi_server?.port || 9696);
        set('config-docs-port', docs_server?.port    || 9697);

        // llama.cpp
        set('config-llama-port',         llama_cpp?.port         || 9780);
        set('config-llama-models-dir',    llama_cpp?.models_dir   || '~/.models');
        set('config-llama-server-path',   llama_cpp?.server_path  || '');
        set('config-llama-default-model', llama_cpp?.default_model || '');
        chk('config-llama-autostart',     llama_cpp?.auto_start);

        // Directories
        set('config-dir-models', dirs.models    || '~/.models');
        set('config-dir-rag',    dirs.rag        || '~/.ai-assist/rag');
        set('config-dir-hf',     dirs.hf_models  || '~/.hf_models');
        set('config-dir-foundry', foundry_ai?.models_dir || '.foundry/cache/models');

        // FTP
        const ftp = data.config?.ftp || {};
        set('config-ftp-host',     ftp.host     || '');
        set('config-ftp-user',     ftp.user     || '');
        set('config-ftp-port',     ftp.port     || 21);
        set('config-ftp-docs-dir', ftp.docs_dir || '');

        // Custom provider
        const custom = data.config?.custom || {};
        set('config-custom-base-url', custom.base_url || '');

        // FastAPI Server
        set('config-api-host',    fastapi_server?.host || '0.0.0.0');
        set('config-api-mode',    fastapi_server?.mode || 'dev');
        set('config-api-workers', fastapi_server?.workers || 1);
        chk('config-api-auto-port', fastapi_server?.auto_find_free_port);

        // Foundry AI
        set('config-foundry-url',    foundry_ai?.base_url      || '');
        set('config-foundry-model',  foundry_ai?.default_model || '');
        set('config-foundry-temp',   foundry_ai?.temperature   || '');
        set('config-foundry-tokens', foundry_ai?.max_tokens    || '');
        chk('config-foundry-autostart', foundry_ai?.auto_start);
        chk('config-foundry-autoload', foundry_ai?.auto_load_default);

        // Startup model mode
        const mode = foundry_ai?.startup_model_mode || 'default';
        const modeEl = document.querySelector(`input[name="startup-model-mode"][value="${mode}"]`);
        if (modeEl) modeEl.checked = true;
        set('config-startup-custom-model', foundry_ai?.startup_custom_model || '');
        document.getElementById('startup-custom-model-row').style.display = mode === 'custom' ? '' : 'none';

        // RAG
        const rag = data.config?.rag_system || {};
        chk('config-rag-enabled', rag.enabled);
        set('config-rag-index', rag.index_dir  || '~/.ai-assist/rag/default_index');
        set('config-rag-chunk', rag.chunk_size || 1000);

        // OpenCode
        const oc = data.config?.opencode || {};
        chk('config-opencode-enabled', oc.enabled ?? true);
        chk('config-opencode-autostart', oc.auto_start ?? false);
        set('config-opencode-version', oc.target_version || '1.15.3');
        set('config-opencode-host', oc.host || '127.0.0.1');
        set('config-opencode-port', oc.port || 4096);
        const ocConnectHost = ['0.0.0.0', '::'].includes(oc.host) ? '127.0.0.1' : (oc.host || '127.0.0.1');
        const ocBaseUrl = (oc.base_url || `http://${ocConnectHost}:${oc.port || 4096}`)
            .replace('://0.0.0.0', '://127.0.0.1')
            .replace('://[::]', '://127.0.0.1');
        set('config-opencode-base-url', ocBaseUrl);
        set('config-opencode-command', oc.command || 'opencode');
        set('config-opencode-username', oc.username || 'opencode');
        set('config-opencode-password', oc.password || '');
        set('config-opencode-cors', (oc.cors || []).join(','));

        // Security
        const sec = data.config?.security || {};
        set('config-security-key', sec.api_key || '');
        chk('config-security-https', sec.https_enabled);

        // Logging
        const log = data.config?.logging || {};
        set('config-log-level',           log.level            || 'INFO');
        set('config-log-file',            log.file             || '');
        set('config-log-max-mb',          log.max_bytes_mb     || 10);
        set('config-log-backup-count',    log.backup_count     || 5);
        set('config-log-structured-file', log.structured_file  || '');
        set('config-log-retention',       log.retention_hours  || 24);
        set('config-log-suppress',        (log.suppress_loggers || []).join(','));
        chk('config-log-console',         log.console          !== false);
        chk('config-log-file-enabled',    log.file_handler     !== false);
        chk('config-log-errors-file',     log.errors_file      !== false);
        chk('config-log-structured',      log.structured       !== false);

        // HuggingFace
        const hf = data.config?.huggingface || {};
        set('config-hf-device',         hf.device     || 'auto');
        set('config-hf-max-tokens',     hf.default_max_new_tokens || 512);
        set('config-hf-default-model',  hf.default_model || '');

        // Docs Server
        chk('config-docs-enabled', docs_server?.enabled);

        // Development
        const dev = data.config?.development || {};
        chk('config-dev-debug',   dev.debug);
        chk('config-dev-verbose', dev.verbose);

        // Text Extractor
        const ext = data.config?.text_extractor || {};
        set('config-extractor-max-size',    ext.max_file_size_mb              ?? 20);
        set('config-extractor-timeout',     ext.processing_timeout_seconds    ?? 300);
        set('config-extractor-ocr-langs',   ext.ocr_languages                 ?? 'rus+eng');
        set('config-extractor-web-timeout', ext.web_page_timeout              ?? 30);
        set('config-extractor-max-images',  ext.max_images_per_page           ?? 20);
        chk('config-extractor-js',          ext.enable_javascript             ?? false);
        chk('config-extractor-limits',      ext.enable_resource_limits        ?? true);

        // Translator
        const tr = data.config?.translator || {};
        const trEnabled = tr.enabled ?? false;
        chk('config-translator-enabled', trEnabled);
        document.getElementById('translator-settings-body').style.display = trEnabled ? '' : 'none';
        set('config-translator-provider',       tr.default_provider              || 'mymemory');
        set('config-translator-timeout',        tr.request_timeout_sec           ?? 30);
        set('config-translator-mymemory-email', tr.mymemory_email                || '');
        set('config-translator-libre-url',      tr.libretranslate_url            || 'https://libretranslate.com');
        set('config-translator-libre-fallback', tr.libretranslate_fallback_url   || 'https://translate.argosopentech.com');
        set('config-translator-libre-key',      tr.libretranslate_api_key        || '');

        showAlert('Settings loaded', 'success');
    } catch (error) {
        showAlert('Failed to load config fields', 'danger');
    }
}

// ── Save fields (Settings tab) ────────────────────────────────────────────────

/**
 * Collect all Settings form values and POST to /api/v1/config.
 */
export async function saveConfigFields() {
    try {
        document.getElementById('config-status')?.style && (document.getElementById('config-status').style.display = 'none');

        const get  = id => document.getElementById(id)?.value || '';
        const getN = (id, def) => parseInt(document.getElementById(id)?.value || def);
        const getF = (id, def) => parseFloat(document.getElementById(id)?.value || def);
        const getC = id => document.getElementById(id)?.checked || false;

        const configData = {
            fastapi_server: {
                host:                get('config-api-host') || '0.0.0.0',
                port:                getN('config-api-port', 9696),
                auto_find_free_port: getC('config-api-auto-port'),
                mode:                get('config-api-mode') || 'dev',
                workers:             getN('config-api-workers', 1),
            },
            foundry_ai: {
                base_url:             get('config-foundry-url'),
                default_model:        get('config-foundry-model'),
                temperature:          getF('config-foundry-temp', 0.7),
                max_tokens:           getN('config-foundry-tokens', 2048),
                auto_start:           getC('config-foundry-autostart'),
                auto_load_default:    getC('config-foundry-autoload'),
                startup_model_mode:   document.querySelector('input[name="startup-model-mode"]:checked')?.value || 'default',
                startup_custom_model: get('config-startup-custom-model'),
                models_dir:           get('config-dir-foundry') || '.foundry/cache/models',
            },
            rag_system: {
                enabled:   getC('config-rag-enabled'),
                index_dir: get('config-rag-index') || '~/.ai-assist/rag/default_index',
                chunk_size:getN('config-rag-chunk', 1000),
            },
            opencode: {
                enabled:        getC('config-opencode-enabled'),
                target_version: get('config-opencode-version') || '1.15.3',
                auto_start:     getC('config-opencode-autostart'),
                host:           get('config-opencode-host') || '127.0.0.1',
                port:           getN('config-opencode-port', 4096),
                base_url:       get('config-opencode-base-url') || `http://${get('config-opencode-host') || '127.0.0.1'}:${getN('config-opencode-port', 4096)}`,
                command:        get('config-opencode-command') || 'opencode',
                username:       get('config-opencode-username') || 'opencode',
                password:       get('config-opencode-password'),
                cors:           get('config-opencode-cors').split(',').map(s => s.trim()).filter(Boolean),
            },
            security: {
                api_key:       get('config-security-key'),
                https_enabled: getC('config-security-https'),
            },
            logging: {
                level:            get('config-log-level')           || 'INFO',
                file:             get('config-log-file'),
                max_bytes_mb:     getN('config-log-max-mb', 10),
                backup_count:     getN('config-log-backup-count', 5),
                structured_file:  get('config-log-structured-file'),
                retention_hours:  getN('config-log-retention', 24),
                suppress_loggers: get('config-log-suppress').split(',').map(s => s.trim()).filter(Boolean),
                console:          getC('config-log-console'),
                file_handler:     getC('config-log-file-enabled'),
                errors_file:      getC('config-log-errors-file'),
                structured:       getC('config-log-structured'),
            },
            development: {
                debug:   getC('config-dev-debug'),
                verbose: getC('config-dev-verbose'),
            },
            translator: {
                enabled:                    getC('config-translator-enabled'),
                default_provider:           get('config-translator-provider')       || 'mymemory',
                request_timeout_sec:        getN('config-translator-timeout', 30),
                mymemory_email:             get('config-translator-mymemory-email'),
                libretranslate_url:         get('config-translator-libre-url')      || 'https://libretranslate.com',
                libretranslate_fallback_url:get('config-translator-libre-fallback') || 'https://translate.argosopentech.com',
                libretranslate_api_key:     get('config-translator-libre-key'),
            },
            docs_server: {
                enabled: getC('config-docs-enabled'),
                port:    getN('config-docs-port', 9697),
            },
            llama_cpp: {
                port:          getN('config-llama-port', 9780),
                host:          '127.0.0.1',
                server_path:   get('config-llama-server-path'),
                models_dir:    get('config-llama-models-dir') || '~/.models',
                default_model: get('config-llama-default-model'),
                auto_start:    getC('config-llama-autostart'),
            },
            ollama: {
                base_url:    window.CONFIG?.ollama_url || 'http://localhost:11434',
                temperature: window.CONFIG?.ollama_temperature ?? 0.7,
                top_p:       window.CONFIG?.ollama_top_p ?? 0.9,
                top_k:       window.CONFIG?.ollama_top_k ?? 50,
                max_tokens:  window.CONFIG?.ollama_max_tokens ?? 2048,
            },
            directories: {
                models:    get('config-dir-models') || '~/.models',
                rag:       get('config-dir-rag')    || '~/.ai-assist/rag',
                hf_models: get('config-dir-hf')     || '~/.hf_models',
            },
            ftp: {
                host:     get('config-ftp-host'),
                user:     get('config-ftp-user'),
                port:     getN('config-ftp-port', 21),
                docs_dir: get('config-ftp-docs-dir'),
            },
            custom: {
                base_url: get('config-custom-base-url'),
                api_key:  '',
            },
            text_extractor: {
                max_file_size_mb:            getN('config-extractor-max-size', 20),
                processing_timeout_seconds:  getN('config-extractor-timeout', 300),
                ocr_languages:               get('config-extractor-ocr-langs') || 'rus+eng',
                web_page_timeout:            getN('config-extractor-web-timeout', 30),
                max_images_per_page:         getN('config-extractor-max-images', 20),
                enable_javascript:           getC('config-extractor-js'),
                enable_resource_limits:      getC('config-extractor-limits'),
            },
        };

        // Collect HuggingFace fields if module is loaded
        if (typeof window.collectHFConfigFields === 'function') {
            configData.huggingface = window.collectHFConfigFields();
        }

        const response = await fetch(`${window.API_BASE}/config`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ config: configData }),
        });

        const data = await response.json();
        if (data.success) {
            showAlert('Configuration saved', 'success');
            await loadConfig();
        } else {
            showAlert(`Save error: ${data.error || data.detail}`, 'danger');
        }
    } catch (error) {
        showAlert(`Save error: ${error.message}`, 'danger');
    }
}

// ── Export / Import ───────────────────────────────────────────────────────────

export async function exportConfig() {
    // Security warning — the export includes the full .env with all secrets
    const confirmed = confirm(
        '⚠️ ВНИМАНИЕ: Экспорт содержит ПОЛНОЕ содержимое .env файла, включая все токены и ключи API.\n\n' +
        'Храните файл бэкапа в безопасном месте и никому не передавайте.\n\n' +
        'Продолжить экспорт?'
    );
    if (!confirmed) return;

    try {
        const data = await fetch(`${window.API_BASE}/config/export`).then(r => r.json());
        const a = Object.assign(document.createElement('a'), {
            href:     URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })),
            download: `aiassist_config_backup_${new Date().toISOString().slice(2,16).replace(/[-T:]/g, (c) => c === 'T' ? '_' : c === '-' ? '' : '')}.json`,
        });
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        showAlert('Configuration exported', 'success');
    } catch (e) {
        showAlert('Export failed', 'danger');
    }
}

export async function importConfig(event) {
    const file = event.target.files[0];
    if (!file) return;
    event.target.value = '';
    try {
        const parsed = JSON.parse(await file.text());
        const merge  = confirm('Merge with current configuration?');
        const result = await fetch(`${window.API_BASE}/config/import`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ config: parsed, merge }),
        }).then(r => r.json());

        if (result.success) {
            showAlert('Configuration imported', 'success');
            await loadConfigFields();
        } else {
            showAlert(`Import error: ${result.error}`, 'danger');
        }
    } catch (e) {
        showAlert('Invalid config file', 'danger');
    }
}

// ── Log health badges (Settings → Logging section) ────────────────────────────

export async function refreshLogHealth() {
    const container = document.getElementById('log-health-badges');
    if (!container) return;
    try {
        const data = await fetch(`${window.API_BASE}/logs/health`).then(r => r.json());
        if (!data.success) throw new Error(data.error || 'failed');
        const m = data.metrics || {};
        const statusColor = { healthy: 'success', warning: 'warning', critical: 'danger', error: 'danger' };
        const color = statusColor[data.status] || 'secondary';
        container.innerHTML = `
            <span class="badge bg-${color}">${data.status}</span>
            <span class="badge bg-secondary"><i class="bi bi-x-circle me-1"></i>${m.errors_count ?? 0} errors</span>
            <span class="badge bg-secondary"><i class="bi bi-exclamation-triangle me-1"></i>${m.warnings_count ?? 0} warnings</span>
            <span class="badge bg-secondary"><i class="bi bi-arrow-left-right me-1"></i>${m.api_requests ?? 0} requests</span>
            <span class="badge bg-secondary"><i class="bi bi-clock me-1"></i>${(m.avg_response_time ?? 0).toFixed(3)}s avg</span>
        `;
    } catch {
        container.innerHTML = '<span class="badge bg-secondary">unavailable</span>';
    }
}
