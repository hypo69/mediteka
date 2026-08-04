// FastAPI Foundry Web Interface
const API_BASE = window.location.origin + '/api/v1';

// Глобальная конфигурация
let CONFIG = {
    foundry_url: 'http://localhost:50477/v1/',
    api_url: API_BASE
};

// Инициализация
document.addEventListener('DOMContentLoaded', async function() {
    await loadConfig();
    await checkSystemStatus();
    await loadModels();
    await loadConnectedModels();
    if (typeof hfUpdateChatModelSelect === 'function') hfUpdateChatModelSelect();
    setInterval(checkSystemStatus, 30000);
});

// Загрузка конфигурации
async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE}/config`);
        const data = await response.json();

        if (data.success) {
            // Обновляем CONFIG с данными из API
            CONFIG.foundry_url = data.foundry_ai.base_url;
            CONFIG.default_model = data.foundry_ai.default_model;
            CONFIG.auto_load_default = data.foundry_ai.auto_load_default || false;

            // Порт llama.cpp из config.json
            const llamaPort = data.config?.llama_cpp?.port;
            if (llamaPort) {
                const el = document.getElementById('llama-port');
                if (el) el.value = llamaPort;
            }
            
            console.log('Config loaded from API:', CONFIG);
            
            // Проверяем доступность модели по умолчанию
            await validateDefaultModel();
        } else {
            console.error('Failed to load config from API:', data.error);
        }
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

// Проверка доступности модели по умолчанию
async function validateDefaultModel() {
    try {
        // Получаем список доступных моделей из Foundry
        const response = await fetch(`${API_BASE}/foundry/models/loaded`);
        const data = await response.json();

        if (data.success && data.models) {
            const availableModels = data.models.map(m => m.id);
            
            if (CONFIG.default_model && availableModels.includes(CONFIG.default_model)) {
                // Модель из config.json доступна - используем её
                updateModelStatus(`Модель по умолчанию: ${CONFIG.default_model}`, 'success');
                const chatModelSelect = document.getElementById('chat-model');
                if (chatModelSelect) {
                    chatModelSelect.value = CONFIG.default_model;
                }
            } else if (availableModels.length > 0) {
                // Есть доступные модели, но не та что в config - предлагаем выбрать
                const firstAvailable = availableModels[0];
                updateModelStatus(`Доступные модели найдены. <button class="btn btn-sm btn-primary ms-2" onclick="selectFoundryModel('${firstAvailable}')">${firstAvailable}</button> <button class="btn btn-sm btn-outline-secondary ms-2" onclick="showAvailableModels()">Показать все</button>`, 'info');
                
                // Автоматически заполняем селектор чата доступными моделями
                const chatModelSelect = document.getElementById('chat-model');
                if (chatModelSelect) {
                    chatModelSelect.innerHTML = '<option value="">Выберите модель...</option>';
                    availableModels.forEach(modelId => {
                        const option = document.createElement('option');
                        option.value = modelId;
                        option.textContent = modelId;
                        chatModelSelect.appendChild(option);
                    });
                }
            } else {
                // Нет доступных моделей
                updateModelStatus('Модели не загружены. <button class="btn btn-sm btn-primary ms-2" onclick="showAvailableModels()">Загрузить модель</button>', 'warning');
            }
        } else {
            updateModelStatus('Не удалось проверить доступные модели. Foundry может быть не запущен.', 'warning');
        }
    } catch (error) {
        console.error('Error validating default model:', error);
        updateModelStatus('Ошибка проверки модели по умолчанию. Проверьте подключение к Foundry.', 'danger');
    }
}

// Загрузка модели по умолчанию
async function loadDefaultModel() {
    try {
        showAlert('Начинаем загрузку модели по умолчанию...', 'info');

        const response = await fetch(`${API_BASE}/foundry/models/auto-load-default`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            // Обновляем статус через несколько секунд
            setTimeout(() => {
                validateDefaultModel();
                loadModels();
            }, 3000);
        } else {
            showAlert(`Ошибка: ${data.error}`, 'danger');
        }
    } catch (error) {
        showAlert('Ошибка загрузки модели', 'danger');
    }
}

// Обновление бейджа выбранной модели
function updateChatModelBadge(modelId) {
    const badge = document.getElementById('chat-model-badge');
    if (!badge) return;
    if (modelId) {
        const label = modelId.startsWith('hf::') ? '🤗 ' + modelId.slice(4) : modelId;
        badge.textContent = label;
        badge.style.display = '';
    } else {
        badge.style.display = 'none';
    }
}

// updateModelStatus — заглушка для обратной совместимости
function updateModelStatus(message, type) {}

// Загрузка конфигурации в отдельные поля
async function loadConfigFields() {
    try {
        const response = await fetch(`${API_BASE}/config`);
        const data = await response.json();

        if (data.success && data.config) {
            const config = data.config;
            
            // FastAPI Server
            document.getElementById('config-api-host').value = config.fastapi_server?.host || '0.0.0.0';
            document.getElementById('config-api-port').value = config.fastapi_server?.port || 9696;
            document.getElementById('config-api-auto-port').checked = config.fastapi_server?.auto_find_free_port || true;
            document.getElementById('config-api-mode').value = config.fastapi_server?.mode || 'dev';
            document.getElementById('config-api-workers').value = config.fastapi_server?.workers || 1;
            
            // Foundry AI
            document.getElementById('config-foundry-url').value = config.foundry_ai?.base_url || 'http://localhost:50477/v1/';
            document.getElementById('config-foundry-model').value = config.foundry_ai?.default_model || '';
            document.getElementById('config-foundry-temp').value = config.foundry_ai?.temperature || 0.6;
            document.getElementById('config-foundry-tokens').value = config.foundry_ai?.max_tokens || 2048;
            document.getElementById('config-foundry-autoload').checked = config.foundry_ai?.auto_load_default || false;
            
            // RAG System
            document.getElementById('config-rag-enabled').checked = config.rag_system?.enabled || false;
            document.getElementById('config-rag-index').value = config.rag_system?.index_dir || './rag_index';
            document.getElementById('config-rag-chunk').value = config.rag_system?.chunk_size || 1000;
            
            // Security
            document.getElementById('config-security-key').value = config.security?.api_key || '';
            document.getElementById('config-security-https').checked = config.security?.https_enabled || false;
            
            // Logging
            document.getElementById('config-log-level').value = config.logging?.level || 'INFO';
            document.getElementById('config-log-file').value = config.logging?.file || 'logs/fastapi-foundry.log';
            
            // Development
            document.getElementById('config-dev-debug').checked = config.development?.debug || false;
            document.getElementById('config-dev-verbose').checked = config.development?.verbose || false;
            
            // Обновляем глобальную конфигурацию
            CONFIG.foundry_url = config.foundry_ai?.base_url || CONFIG.foundry_url;
            CONFIG.default_model = config.foundry_ai?.default_model || CONFIG.default_model;
            CONFIG.auto_load_default = config.foundry_ai?.auto_load_default || false;
            
            console.log('Config fields loaded successfully');
            showAlert('Configuration loaded', 'success');
        }
    } catch (error) {
        console.error('Failed to load config fields:', error);
        showAlert('Failed to load configuration', 'danger');
    }
}

// Сохранение конфигурации из отдельных полей
async function saveConfigFields() {
    const statusDiv = document.getElementById('config-status');

    try {
        // Функция для безопасного получения значения
        const getValue = (id, defaultValue = null) => {
            const element = document.getElementById(id);
            if (!element) return defaultValue;
            const value = element.value;
            return (value === '') ? null : value;
        };
        
        const getIntValue = (id, defaultValue = null) => {
            const value = getValue(id);
            if (value === null || value === '') return defaultValue;
            const parsed = parseInt(value);
            return isNaN(parsed) ? defaultValue : parsed;
        };
        
        const getFloatValue = (id, defaultValue = null) => {
            const value = getValue(id);
            if (value === null || value === '') return defaultValue;
            const parsed = parseFloat(value);
            return isNaN(parsed) ? defaultValue : parsed;
        };
        
        const getBoolValue = (id, defaultValue = false) => {
            const element = document.getElementById(id);
            return element ? element.checked : defaultValue;
        };
        
        // Собираем конфигурацию из полей с валидацией
        const configData = {
            fastapi_server: {
                host: getValue('config-api-host') || '0.0.0.0',
                port: getIntValue('config-api-port') || 9696,
                auto_find_free_port: getBoolValue('config-api-auto-port', true),
                mode: getValue('config-api-mode') || 'dev',
                workers: getIntValue('config-api-workers') || 1,
                reload: true,
                cors_origins: ["*"]
            },
            foundry_ai: {
                base_url: getValue('config-foundry-url') || 'http://localhost:50477/v1/',
                default_model: getValue('config-foundry-model'),
                auto_load_default: getBoolValue('config-foundry-autoload', false),
                temperature: getFloatValue('config-foundry-temp') || 0.6,
                top_p: 0.9,
                top_k: 40,
                max_tokens: getIntValue('config-foundry-tokens') || 2048,
                timeout: 300
            },
            rag_system: {
                enabled: getBoolValue('config-rag-enabled', false),
                index_dir: getValue('config-rag-index') || './rag_index',
                model: "sentence-transformers/all-MiniLM-L6-v2",
                chunk_size: getIntValue('config-rag-chunk') || 1000,
                top_k: 5
            },
            security: {
                api_key: getValue('config-security-key'),
                https_enabled: getBoolValue('config-security-https', false),
                cors_origins: ["*"],
                ssl_cert_file: "~/.ssl/cert.pem",
                ssl_key_file: "~/.ssl/key.pem"
            },
            logging: {
                level: getValue('config-log-level') || 'INFO',
                file: getValue('config-log-file') || 'logs/fastapi-foundry.log'
            },
            development: {
                debug: getBoolValue('config-dev-debug', false),
                verbose: getBoolValue('config-dev-verbose', false),
                temp_dir: "./temp"
            }
        };
        
        // Получаем полную текущую конфигурацию и обновляем только измененные поля
        const currentResponse = await fetch(`${API_BASE}/config`);
        const currentData = await currentResponse.json();
        
        if (currentData.success && currentData.config) {
            // Объединяем с существующими данными
            const fullConfig = { ...currentData.config };
            
            // Обновляем только измененные поля
            Object.keys(configData).forEach(section => {
                if (fullConfig[section]) {
                    fullConfig[section] = { ...fullConfig[section], ...configData[section] };
                } else {
                    fullConfig[section] = configData[section];
                }
            });
            
            console.log('Saving config fields:', Object.keys(configData));
            
            const response = await fetch(`${API_BASE}/config`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({config: fullConfig})
            });
            
            const result = await response.json();
            
            if (result && result.success) {
                statusDiv.className = 'alert alert-success';
                statusDiv.innerHTML = `<i class="bi bi-check-circle"></i> ${result.message || 'Configuration saved'}`;
                if (result.backup_created) {
                    statusDiv.innerHTML += `<br><small>Backup: ${result.backup_created}</small>`;
                }
                statusDiv.style.display = 'block';
                
                // Обновляем глобальную конфигурацию
                CONFIG.foundry_url = configData.foundry_ai.base_url;
                CONFIG.default_model = configData.foundry_ai.default_model;
                CONFIG.auto_load_default = configData.foundry_ai.auto_load_default;
                
                showAlert('Configuration saved successfully', 'success');
                
                // Перепроверяем модель по умолчанию
                setTimeout(() => {
                    validateDefaultModel();
                }, 1000);
            } else {
                statusDiv.className = 'alert alert-danger';
                statusDiv.innerHTML = `<i class="bi bi-exclamation-triangle"></i> Error: ${result?.error || 'Unknown error'}`;
                statusDiv.style.display = 'block';
                showAlert(`Error: ${result?.error || 'Unknown error'}`, 'danger');
            }
        } else {
            throw new Error('Failed to load current configuration');
        }
    } catch (error) {
        console.error('Save config error:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack
        });
        
        statusDiv.className = 'alert alert-danger';
        statusDiv.innerHTML = `<i class="bi bi-exclamation-triangle"></i> Error: ${error.message}`;
        statusDiv.style.display = 'block';
        showAlert(`Error: ${error.message}`, 'danger');
    }
    
    // Скрыть статус через 10 секунд
    setTimeout(() => {
        if (statusDiv) {
            statusDiv.style.display = 'none';
        }
    }, 10000);
}

// Проверка статуса системы
async function checkSystemStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        const indicator = document.getElementById('status-indicator');
        
        if (response.ok && data.status === 'healthy') {
            if (data.foundry_status === 'healthy') {
                indicator.innerHTML = '<i class="bi bi-circle-fill text-success"></i> Connected';
            } else {
                indicator.innerHTML = '<i class="bi bi-circle-fill text-warning"></i> API Only';
            }
        } else {
            indicator.innerHTML = '<i class="bi bi-circle-fill text-danger"></i> Error';
        }
        
        updateSystemInfo(data);

        // Обновляем UI вкладки Foundry из тех же данных —
        // без отдельного запроса к /foundry/status
        if (data.foundry_status === 'healthy' && data.foundry_details) {
            updateFoundryStatus('running', {
                port: data.foundry_details.port,
                url: data.foundry_details.url
            });
        } else {
            updateFoundryStatus('stopped');
        }

    } catch (error) {
        console.error('System status check failed:', error);
        const indicator = document.getElementById('status-indicator');
        if (indicator) {
            indicator.innerHTML = '<i class="bi bi-circle-fill text-danger"></i> Offline';
        }
        
        const container = document.getElementById('system-status');
        if (container) {
            container.innerHTML = `
                <div class="text-center text-danger">
                    <i class="bi bi-exclamation-triangle"></i><br>
                    <strong>Connection Error</strong><br>
                    <small>Cannot connect to API server</small>
                </div>
            `;
        }

        updateFoundryStatus('error');
    }
}

// Обновление информации о системе
function updateSystemInfo(data) {
    const container = document.getElementById('system-status');

    // Получаем реальный порт и URL из данных API
    let foundryUrl = 'Not connected';
    let foundryPort = 'Unknown';
    
    if (data.foundry_details) {
        if (data.foundry_details.url) {
            foundryUrl = data.foundry_details.url;
            CONFIG.foundry_url = foundryUrl; // Обновляем глобальную конфигурацию
        }
        if (data.foundry_details.port) {
            foundryPort = data.foundry_details.port;
        }
    }
    
    const foundryStatusText = data.foundry_status === 'healthy' ? 'Connected' : 
                             data.foundry_status === 'disconnected' ? 'Disconnected' :
                             data.foundry_status === 'error' ? 'Error' : 'Unknown';
    
    const foundryBadgeClass = data.foundry_status === 'healthy' ? 'bg-success' : 
                             data.foundry_status === 'disconnected' ? 'bg-warning' : 'bg-danger';
    
    container.innerHTML = `
        <div class="row">
            <div class="col-6">
                <strong>API:</strong><br>
                <span class="badge ${data.status === 'healthy' ? 'bg-success' : 'bg-danger'}">${data.status}</span>
            </div>
            <div class="col-6">
                <strong>Foundry:</strong><br>
                <span class="badge ${foundryBadgeClass}">${foundryStatusText}</span>
            </div>
            <div class="col-12 mt-2">
                <strong>Foundry URL:</strong><br>
                <small class="text-muted">${foundryUrl}</small>
            </div>
            <div class="col-12 mt-1">
                <strong>Port:</strong> <span class="badge bg-info">${foundryPort}</span>
                <strong class="ms-3">Models:</strong> <span class="badge bg-secondary">${data.models_count || 0}</span>
            </div>
        </div>
    `;
}

// Загрузка моделей
async function loadModels() {
    try {
        const response = await fetch(`${API_BASE}/models`);
        const data = await response.json();

        if (data.success && data.models) {
            updateModelSelect(data.models);
        }
    } catch (error) {
        console.error('Failed to load models:', error);
    }
}

// Загрузка подключенных моделей для таба Models
async function loadConnectedModels() {
    try {
        const response = await fetch(`${API_BASE}/models/connected`);
        const data = await response.json();

        const container = document.getElementById('models-container');
        
        if (data.success && data.models && data.models.length > 0) {
            container.innerHTML = data.models.map(model => `
                <div class="col-md-6 col-lg-4 mb-3">
                    <div class="card model-card h-100">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="card-title mb-0">${model.name}</h6>
                                <span class="badge ${
                                    model.status === 'connected' ? 'bg-success' : 
                                    model.status === 'offline' ? 'bg-danger' : 'bg-secondary'
                                }">${model.status}</span>
                            </div>
                            <p class="card-text">
                                <small class="text-muted">ID: ${model.id}</small><br>
                                <small class="text-muted">Provider: ${model.provider}</small><br>
                                <small class="text-muted">Max tokens: ${model.max_tokens || 'N/A'}</small>
                            </p>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="default-model" id="default-${model.id}" value="${model.id}" ${CONFIG.default_model === model.id ? 'checked' : ''} onchange="setDefaultModel('${model.id}')">
                                <label class="form-check-label" for="default-${model.id}">
                                    <small>Use as default model</small>
                                </label>
                            </div>
                        </div>
                        <div class="card-footer bg-transparent">
                            <div class="btn-group w-100" role="group">
                                <button class="btn btn-sm btn-primary" onclick="selectModelForChat('${model.id}')">
                                    <i class="bi bi-chat"></i> Use in Chat
                                </button>
                                <button class="btn btn-sm btn-outline-secondary" onclick="testModel('${model.id}')">
                                    <i class="bi bi-play"></i> Test
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="removeModel('${model.id}')">
                                    <i class="bi bi-trash"></i> Remove
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="col-12">
                    <div class="text-center text-muted py-5">
                        <i class="bi bi-cpu" style="font-size: 3rem;"></i><br>
                        <h5>No Connected Models</h5>
                        <p>No models are currently connected. ${data.error ? `Error: ${data.error}` : 'Start Foundry and load a model to see it here.'}</p>
                        <button class="btn btn-primary" onclick="refreshModels()">
                            <i class="bi bi-arrow-clockwise"></i> Refresh
                        </button>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to load connected models:', error);
        document.getElementById('models-container').innerHTML = `
            <div class="col-12">
                <div class="text-center text-danger py-5">
                    <i class="bi bi-exclamation-triangle" style="font-size: 3rem;"></i><br>
                    <h5>Error Loading Models</h5>
                    <p>Failed to connect to the API. Make sure the server is running.</p>
                    <button class="btn btn-outline-primary" onclick="refreshModels()">
                        <i class="bi bi-arrow-clockwise"></i> Try Again
                    </button>
                </div>
            </div>
        `;
    }
}

// Выбор модели для чата
function selectModelForChat(modelId) {
    const chatModelSelect = document.getElementById('chat-model');
    if (chatModelSelect) {
        // Проверяем есть ли такая опция
        let optionExists = false;
        for (let option of chatModelSelect.options) {
            if (option.value === modelId) {
                optionExists = true;
                break;
            }
        }

        // Если опции нет, добавляем
        if (!optionExists) {
            const option = document.createElement('option');
            option.value = modelId;
            option.textContent = modelId;
            chatModelSelect.appendChild(option);
        }
        
        // Выбираем модель
        chatModelSelect.value = modelId;
        
        // Сохраняем как модель по умолчанию
        saveDefaultModel(modelId);
        
        showAlert(`Model ${modelId} selected for chat`, 'success');
        
        // Переключаемся на вкладку чата
        const chatTab = document.getElementById('chat-tab');
        if (chatTab) {
            chatTab.click();
        }
    }
}

// Тест модели
async function testModel(modelId) {
    try {
        showAlert(`Testing model ${modelId}...`, 'info');

        // Получаем актуальный статус Foundry для правильного URL
        const healthResponse = await fetch(`${API_BASE}/health`);
        const healthData = await healthResponse.json();
        
        let foundryUrl = CONFIG.foundry_url;
        if (healthData.foundry_details && healthData.foundry_details.url) {
            foundryUrl = healthData.foundry_details.url;
        }
        
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                prompt: 'Hello! Please respond with a short greeting.',
                model: modelId,
                max_tokens: 50
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(`Model ${modelId} test successful: "${data.content.substring(0, 100)}..."`, 'success');
        } else {
            showAlert(`Model ${modelId} test failed: ${data.error}`, 'danger');
        }
    } catch (error) {
        showAlert(`Model ${modelId} test error: ${error.message}`, 'danger');
    }
}

// Обновление списка моделей
function updateModelSelect(models) {
    const select = document.getElementById('chat-model');
    if (!select) return;

    // Сохраняем HF-опции (optgroup и отдельные опции с data-hf)
    const hfGroups = [...select.querySelectorAll('optgroup')];
    const hfOptions = [...select.options].filter(o => o.dataset.hf);

    select.innerHTML = '<option value="">Auto-select</option>';
    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = model.id;
        select.appendChild(option);
    });

    // Восстанавливаем HF-опции
    hfGroups.forEach(g => select.appendChild(g));
    hfOptions.filter(o => !o.closest('optgroup')).forEach(o => select.appendChild(o));

    // Автоматически выбираем модель по умолчанию если она доступна
    if (CONFIG.default_model) {
        const availableModels = models.map(m => m.id);
        if (availableModels.includes(CONFIG.default_model)) {
            select.value = CONFIG.default_model;
            updateChatModelBadge(CONFIG.default_model);
        }
    }
}

// Отправка сообщения
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    addMessageToChat('user', message);
    input.value = '';

    const typingId = addMessageToChat('assistant', '<i class="bi bi-three-dots"></i> Typing...');
    const _chatStart = Date.now();
    const _timerEl = document.getElementById('chat-timer');
    const _timerVal = document.getElementById('chat-timer-value');
    if (_timerEl) _timerEl.style.display = '';
    const _timerInterval = setInterval(() => {
        if (_timerVal) _timerVal.textContent = ((Date.now() - _chatStart) / 1000).toFixed(1) + 's';
    }, 100);

    try {
        const selectedModel = document.getElementById('chat-model').value || '';
        const temperature   = parseFloat(document.getElementById('temperature').value);
        const maxTokens     = parseInt(document.getElementById('max-tokens').value);

        let data;
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), 300000);
        try {
            if (selectedModel.startsWith('hf::')) {
                const modelId = selectedModel.slice(4);
                const res = await fetch(`${API_BASE}/hf/generate`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ model_id: modelId, prompt: message, max_new_tokens: maxTokens, temperature }),
                    signal: ctrl.signal
                });
                data = await res.json();
            } else {
                const res = await fetch(`${API_BASE}/generate`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ prompt: message, model: selectedModel || undefined, temperature, max_tokens: maxTokens }),
                    signal: ctrl.signal
                });
                data = await res.json();
            }
        } finally {
            clearTimeout(timer);
            clearInterval(_timerInterval);
            if (_timerEl) {
                const elapsed = ((Date.now() - _chatStart) / 1000).toFixed(1) + 's';
                _timerVal.textContent = elapsed;
                _timerEl.style.display = '';
            }
        }

        document.getElementById(typingId).remove();
        if (data.success && data.content) {
            addMessageToChat('assistant', data.content);
        } else {
            addMessageToChat('assistant', `❌ Error: ${data.error || 'Failed to generate response'}`);
        }
    } catch (error) {
        clearInterval(_timerInterval);
        if (_timerEl) _timerEl.style.display = 'none';
        document.getElementById(typingId).remove();
        addMessageToChat('assistant', '❌ Connection error');
    }
}

// Добавление сообщения в чат
function addMessageToChat(role, content) {
    const container = document.getElementById('chat-messages');
    const messageId = 'msg-' + Date.now();

    if (container.children.length === 1 && container.children[0].classList.contains('text-muted')) {
        container.innerHTML = '';
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = `<div class="content">${content}</div>`;
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
    
    return messageId;
}

// Foundry Status Check
async function checkFoundryStatus() {
    try {
        const response = await fetch(`${API_BASE}/foundry/status`);
        const data = await response.json();

        if (data.running) {
            updateFoundryStatus('running', data);
        } else {
            updateFoundryStatus('stopped');
        }
    } catch (error) {
        updateFoundryStatus('error');
    }
}

function updateFoundryStatus(status, data = {}) {
    const badge = document.getElementById('foundry-service-status');
    const portIndicator = document.getElementById('foundry-port-indicator');
    const info = document.getElementById('foundry-service-info');
    const startBtn = document.getElementById('foundry-start-btn');
    const stopBtn = document.getElementById('foundry-stop-btn');

    switch (status) {
        case 'running':
            badge.className = 'badge bg-success';
            badge.textContent = 'Running';
            if (data.port && data.port !== 'Unknown') {
                portIndicator.className = 'badge bg-info me-2';
                portIndicator.textContent = `Port: ${data.port}`;
                info.innerHTML = `<small>Foundry API: ${data.url || `http://localhost:${data.port}/v1/`}</small>`;
            } else {
                portIndicator.className = 'badge bg-warning me-2';
                portIndicator.textContent = 'Port: Detecting...';
                info.innerHTML = '<small>Foundry is running, detecting port...</small>';
            }
            startBtn.disabled = true;
            stopBtn.disabled = false;
            break;
        case 'stopped':
            badge.className = 'badge bg-secondary';
            badge.textContent = 'Stopped';
            portIndicator.className = 'badge bg-secondary me-2';
            portIndicator.textContent = 'Port: Unknown';
            info.innerHTML = '<small>Foundry service is not running</small>';
            startBtn.disabled = false;
            stopBtn.disabled = true;
            break;
        default:
            badge.className = 'badge bg-danger';
            badge.textContent = 'Error';
            portIndicator.className = 'badge bg-secondary me-2';
            portIndicator.textContent = 'Port: Unknown';
            info.innerHTML = '<small>Error checking Foundry status</small>';
            startBtn.disabled = false;
            stopBtn.disabled = false;
            break;
    }
}

async function startFoundryService() {
    try {
        showAlert('Starting Foundry service...', 'info');
        const response = await fetch(`${API_BASE}/foundry/start`, {
            method: 'POST'
        });
        const data = await response.json();

        if (response.ok) {
            showAlert(data.message, 'success');
            setTimeout(checkFoundryStatus, 3000);
        } else {
            showAlert(`Error: ${data.detail}`, 'danger');
        }
    } catch (error) {
        showAlert('Error starting Foundry service', 'danger');
    }
}

async function stopFoundryService() {
    try {
        showAlert('Stopping Foundry service...', 'info');
        const response = await fetch(`${API_BASE}/foundry/stop`, {
            method: 'POST'
        });
        const data = await response.json();

        if (response.ok) {
            showAlert(data.message, 'success');
            setTimeout(checkFoundryStatus, 2000);
        } else {
            showAlert(`Error: ${data.detail}`, 'danger');
        }
    } catch (error) {
        showAlert('Error stopping Foundry service', 'danger');
    }
}

// Утилиты
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    alertDiv.innerHTML = `${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;

    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 5000);
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function updateTempValue(value) {
    document.getElementById('temp-value').textContent = value;
}

function clearChat() {
    document.getElementById('chat-messages').innerHTML = `<div class="text-muted text-center">
            <i class="bi bi-chat-square-dots"></i><br>
            Start a conversation with AI
        </div>`;
}

function refreshModels() {
    loadModels();
    loadConnectedModels(); // Добавляем загрузку подключенных моделей
}

// Функции для вкладки Logs
async function refreshLogs() {
    const container = document.getElementById('logs-container');
    const levelFilter = document.getElementById('log-level-filter')?.value || '';
    container.innerHTML = '<div class="text-center p-4"><div class="spinner-border spinner-border-sm"></div> Loading...</div>';
    try {
        const res = await fetch(`${API_BASE}/logs?lines=200`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (!data.success || !data.logs?.length) {
            container.innerHTML = '<div class="text-center text-muted p-4"><i class="bi bi-file-text"></i><br>Логи пусты или файл не найден</div>';
            updateLogsStats([]);
            return;
        }

        // Парсим строки логов в объекты {level, timestamp, message}
        const parsed = data.logs.map(line => {
            const m = line.match(/^(\S+\s+\S+)\s+\|(\w+)\s+\|.*?\|\s*(.*)$/);
            if (m) return { timestamp: m[1], level: m[2].toLowerCase(), message: m[3] };
            // fallback — определяем уровень по ключевым словам
            const lvl = /ERROR|CRITICAL/i.test(line) ? 'error'
                      : /WARNING/i.test(line) ? 'warning'
                      : /DEBUG/i.test(line) ? 'debug' : 'info';
            return { timestamp: '', level: lvl, message: line };
        });

        const filtered = levelFilter ? parsed.filter(l => l.level === levelFilter) : parsed;

        container.innerHTML = filtered.map(l => `
            <div class="log-entry log-${l.level}">
                ${l.timestamp ? `<span class="log-timestamp">${l.timestamp}</span> ` : ''}
                <span class="log-message">${l.message}</span>
            </div>`).join('');

        container.scrollTop = container.scrollHeight;
        updateLogsStats(parsed);

    } catch (error) {
        container.innerHTML = `<div class="text-center text-danger p-4"><i class="bi bi-exclamation-triangle"></i><br>Ошибка: ${error.message}</div>`;
    }
}

function updateLogsStats(logs) {
    const healthContainer = document.getElementById('logs-health-status');
    const errorContainer = document.getElementById('error-summary');
    const perfContainer = document.getElementById('performance-metrics');

    // Подсчет по уровням
    const stats = {
        error: logs.filter(l => l.level === 'error').length,
        warning: logs.filter(l => l.level === 'warning').length,
        info: logs.filter(l => l.level === 'info').length,
        debug: logs.filter(l => l.level === 'debug').length
    };
    
    // Статус системы
    const healthStatus = stats.error > 0 ? 'critical' : (stats.warning > 0 ? 'warning' : 'healthy');
    const healthColor = healthStatus === 'critical' ? 'danger' : (healthStatus === 'warning' ? 'warning' : 'success');
    
    healthContainer.innerHTML = `
        <div class="text-center">
            <i class="bi bi-heart-fill text-${healthColor}" style="font-size: 2rem;"></i><br>
            <strong class="text-${healthColor}">${healthStatus.toUpperCase()}</strong><br>
            <small>Всего записей: ${logs.length}</small>
        </div>
    `;
    
    // Ошибки
    errorContainer.innerHTML = `
        <div class="mb-2">
            <span class="badge bg-danger">${stats.error}</span> Ошибок
        </div>
        <div class="mb-2">
            <span class="badge bg-warning">${stats.warning}</span> Предупреждений
        </div>
        <div>
            <span class="badge bg-info">${stats.info}</span> Информационных
        </div>
    `;
    
    // Производительность
    perfContainer.innerHTML = `
        <div class="mb-2">
            <small>Последние записи:</small><br>
            <strong>${logs.length}</strong>
        </div>
        <div>
            <small>Статус:</small><br>
            <span class="badge bg-${healthColor}">${healthStatus}</span>
        </div>
    `;
}

function filterLogs() {
    const filter = document.getElementById('log-level-filter').value;
    const entries = document.querySelectorAll('.log-entry');

    entries.forEach(entry => {
        if (!filter || entry.classList.contains(`log-${filter}`)) {
            entry.style.display = 'block';
        } else {
            entry.style.display = 'none';
        }
    });
}

function clearLogsView() {
    document.getElementById('logs-container').innerHTML = `<div class="text-muted text-center p-4">
            <i class="bi bi-file-text"></i><br>
            Логи очищены. Нажмите "Обновить" для загрузки.
        </div>`;
}

// Автообновление логов каждые 30 секунд
document.addEventListener('DOMContentLoaded', function() {
    // При переключении на вкладку Models
    const modelsTab = document.getElementById('models-tab');
    if (modelsTab) {
        modelsTab.addEventListener('click', function() {
            setTimeout(loadConnectedModels, 100); // Небольшая задержка
        });
    }

    // При переключении на вкладку Foundry
    const foundryTab = document.getElementById('foundry-tab');
    if (foundryTab) {
        foundryTab.addEventListener('click', function() {
            setTimeout(() => {
                checkFoundryStatus();
                listFoundryModels();
            }, 100);
        });
    }
    
    // При переключении на вкладку Logs
    const logsTab = document.getElementById('logs-tab');
    if (logsTab) {
        logsTab.addEventListener('click', function() {
            setTimeout(refreshLogs, 100); // Небольшая задержка
        });
    }
    
    // При переключении на вкладку RAG
    const ragTab = document.getElementById('rag-tab');
    if (ragTab) {
        ragTab.addEventListener('click', function() {
            setTimeout(refreshRAGStatus, 100);
        });
    }
    
    // При переключении на вкладку Settings
    const settingsTab = document.getElementById('settings-tab');
    if (settingsTab) {
        settingsTab.addEventListener('click', function() {
            setTimeout(loadConfigFields, 100); // Загружаем конфигурацию в поля
        });
    }
    
    // Автообновление моделей при открытии вкладки Chat
    document.getElementById('chat-tab')?.addEventListener('shown.bs.tab', loadModels);
    const chatModelSelect = document.getElementById('chat-model');
    if (chatModelSelect) {
        chatModelSelect.addEventListener('change', function() {
            const selectedModel = this.value;
            updateChatModelBadge(selectedModel);
            if (selectedModel && selectedModel !== CONFIG.default_model) {
                saveDefaultModel(selectedModel);
            }
        });
    }
});

// Управление моделями Foundry
async function listFoundryModels() {
    try {
        const response = await fetch(`${API_BASE}/foundry/models/loaded`);
        const data = await response.json();

        const container = document.getElementById('foundry-models-list');
        
        if (data.success && data.models.length > 0) {
            container.innerHTML = data.models.map(model => `
                <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                    <div>
                        <strong>${model.id}</strong><br>
                        <small class="text-muted">Статус: ${model.status}</small>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-primary me-2" onclick="selectFoundryModel('${model.id}')">
                            <i class="bi bi-check-circle"></i> Использовать
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="removeFoundryModel('${model.id}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="text-center text-muted py-3">
                    <i class="bi bi-inbox"></i><br>
                    Модели не загружены<br>
                    <small>Используйте "Загрузить модель" ниже</small>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to list Foundry models:', error);
        showAlert('Ошибка получения списка моделей', 'danger');
    }
}

async function downloadAndRunModel() {
    const select = document.getElementById('model-select');
    const modelId = select.value;

    if (!modelId) {
        showAlert('Выберите модель для загрузки', 'warning');
        return;
    }
    
    const progressDiv = document.getElementById('download-progress');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    try {
        // Показываем прогресс
        progressDiv.style.display = 'block';
        progressBar.style.width = '10%';
        progressText.textContent = `Начинаем загрузку ${modelId}...`;
        
        showAlert(`Началась загрузка модели ${modelId}...`, 'info');
        
        const response = await fetch(`${API_BASE}/foundry/models/load`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({model_id: modelId})
        });
        
        const data = await response.json();
        
        if (data.success) {
            progressBar.style.width = '30%';
            progressText.textContent = `Загрузка ${modelId} в процессе...`;
            
            showAlert(data.message, 'success');
            
            // Начинаем отслеживание прогресса
            monitorModelDownload(modelId, progressBar, progressText, progressDiv);
        } else {
            progressDiv.style.display = 'none';
            showAlert(`Ошибка: ${data.error}`, 'danger');
        }
    } catch (error) {
        progressDiv.style.display = 'none';
        showAlert('Ошибка загрузки модели', 'danger');
        console.error('Download error:', error);
    }
}

// Отслеживание прогресса загрузки модели
async function monitorModelDownload(modelId, progressBar, progressText, progressDiv) {
    let attempts = 0;
    const maxAttempts = 60; // 5 минут (по 5 секунд)
    let currentProgress = 30;

    const checkInterval = setInterval(async () => {
        attempts++;
        
        try {
            // Проверяем статус модели
            const response = await fetch(`${API_BASE}/foundry/models/status/${modelId}`);
            const data = await response.json();
            
            if (data.success) {
                if (data.status === 'loaded') {
                    // Модель загружена!
                    clearInterval(checkInterval);
                    progressBar.style.width = '100%';
                    progressText.textContent = `Модель ${modelId} успешно загружена!`;
                    
                    setTimeout(() => {
                        progressDiv.style.display = 'none';
                        showAlert(`Модель ${modelId} готова к использованию!`, 'success');
                        
                        // Обновляем списки
                        listFoundryModels();
                        loadModels();
                    }, 2000);
                    
                    return;
                } else {
                    // Модель еще загружается
                    currentProgress = Math.min(currentProgress + 2, 90);
                    progressBar.style.width = currentProgress + '%';
                    progressText.textContent = `Загрузка ${modelId}... (${attempts}/${maxAttempts})`;
                }
            }
            
            // Проверяем таймаут
            if (attempts >= maxAttempts) {
                clearInterval(checkInterval);
                progressBar.classList.add('bg-warning');
                progressText.textContent = `Загрузка ${modelId} занимает больше времени чем ожидалось...`;
                
                showAlert(`Загрузка ${modelId} продолжается в фоне. Проверьте логи Foundry.`, 'warning');
                
                setTimeout(() => {
                    progressDiv.style.display = 'none';
                }, 5000);
            }
            
        } catch (error) {
            console.error('Error checking model status:', error);
            // Продолжаем проверку несмотря на ошибку
        }
    }, 5000); // Проверяем каждые 5 секунд
}

async function removeFoundryModel(modelId) {
    if (!confirm(`Удалить модель ${modelId}?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/foundry/models/unload`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({model_id: modelId})
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            listFoundryModels();
            loadModels();
        } else {
            showAlert(`Ошибка: ${data.error}`, 'danger');
        }
    } catch (error) {
        showAlert('Ошибка удаления модели', 'danger');
    }
}

function selectFoundryModel(modelId) {
    // Устанавливаем модель в чате
    const chatModelSelect = document.getElementById('chat-model');
    if (chatModelSelect) {
        // Проверяем есть ли такая опция
        let optionExists = false;
        for (let option of chatModelSelect.options) {
            if (option.value === modelId) {
                optionExists = true;
                break;
            }
        }

        // Если опции нет, добавляем
        if (!optionExists) {
            const option = document.createElement('option');
            option.value = modelId;
            option.textContent = modelId;
            chatModelSelect.appendChild(option);
        }
        
        // Выбираем модель
        chatModelSelect.value = modelId;
        
        // Сохраняем как модель по умолчанию
        saveDefaultModel(modelId);
        
        showAlert(`Модель ${modelId} выбрана как модель по умолчанию`, 'success');
        
        // Переключаемся на вкладку чата
        const chatTab = document.getElementById('chat-tab');
        if (chatTab) {
            chatTab.click();
        }
    }
}

// Установка модели по умолчанию через radio кнопку
function setDefaultModel(modelId) {
    saveDefaultModel(modelId);
    showAlert(`Модель ${modelId} установлена как модель по умолчанию`, 'success');

    // Обновляем глобальную конфигурацию
    CONFIG.default_model = modelId;
    
    // Обновляем селектор в чате
    const chatModelSelect = document.getElementById('chat-model');
    if (chatModelSelect) {
        chatModelSelect.value = modelId;
    }
    
    // Обновляем статус модели
    updateModelStatus(`Модель по умолчанию: ${modelId}`, 'success');
}

// Сохранение модели по умолчанию в config.json
async function saveDefaultModel(modelId) {
    try {
        // Получаем текущую конфигурацию
        const response = await fetch(`${API_BASE}/config`);
        const data = await response.json();

        if (data.success && data.config) {
            // Обновляем модель по умолчанию
            data.config.foundry_ai.default_model = modelId;
            
            // Сохраняем конфигурацию
            const saveResponse = await fetch(`${API_BASE}/config`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({config: data.config})
            });
            
            const saveResult = await saveResponse.json();
            if (saveResult.success) {
                console.log(`Default model saved: ${modelId}`);
                // Обновляем глобальную конфигурацию
                CONFIG.default_model = modelId;
            } else {
                console.error('Failed to save default model:', saveResult.error);
            }
        }
    } catch (error) {
        console.error('Error saving default model:', error);
    }
}

function showModelInfo() {
    const select = document.getElementById('model-select');
    const modelId = select.value;

    if (!modelId) {
        showAlert('Выберите модель для получения информации', 'warning');
        return;
    }
    
    const modelInfo = {
        'qwen3-0.6b-generic-cpu:4:4': 'Самая легкая CPU модель (0.8 GB). Быстрая и эффективная.',
        'qwen2.5-1.5b-instruct-generic-cpu:4': 'Средняя CPU модель (1.78 GB). Хороший баланс скорости и качества.',
        'deepseek-r1-distill-qwen-7b-generic-cpu:3': 'Продвинутая CPU модель (6.43 GB). Высокое качество ответов. (Недоступна)',
        'phi-3-mini-4k-instruct-openvino-gpu:1': 'GPU модель (2.4 GB). Требует совместимую видеокарту.'
    };
    
    const info = modelInfo[modelId] || 'Информация о модели недоступна';
    showAlert(info, 'info');
}

// Пропустить автозагрузку
function skipAutoLoad() {
    const modelName = CONFIG.default_model.split(':')[0];
    updateModelStatus(`Модель "${modelName}" недоступна. <button class="btn btn-sm btn-primary ms-2" onclick="loadDefaultModel()">Загрузить</button> <button class="btn btn-sm btn-outline-secondary ms-2" onclick="showAvailableModels()">Показать доступные</button>`, 'warning');
}

// Показать доступные модели
function showAvailableModels() {
    // Переключаемся на вкладку Foundry
    const foundryTab = document.getElementById('foundry-tab');
    if (foundryTab) {
        foundryTab.click();
        // Показываем список моделей
        setTimeout(() => {
            listFoundryModels();
        }, 100);
    }
    showAlert('Переключились на вкладку Foundry для просмотра доступных моделей', 'info');
}

// Скрыть прогресс-бар
function hideProgress() {
    const progressDiv = document.getElementById('download-progress');
    if (progressDiv) {
        progressDiv.style.display = 'none';
    }
}

// Очистка вывода примеров
function clearExampleOutput() {
    document.getElementById('example-output').innerHTML = `<div class="text-muted text-center mt-5">
            <i class="bi bi-play-circle" style="font-size: 2rem;"></i><br>
            Выберите пример SDK для запуска
        </div>`;
    document.getElementById('example-status').innerHTML = `<div class="text-muted text-center">
            <i class="bi bi-clock"></i><br>
            Ready to run SDK examples
        </div>`;
}

// Запуск SDK примеров
async function runSDKExample(type) {
    const outputDiv = document.getElementById('example-output');
    const statusDiv = document.getElementById('example-status');

    outputDiv.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><br>Запуск SDK примера...</div>';
    statusDiv.innerHTML = '<div class="text-warning"><i class="bi bi-play-circle"></i> Выполняется...</div>';
    
    try {
        let endpoint = '';
        let description = '';
        
        switch(type) {
            case 'basic':
                endpoint = '/api/v1/examples/sdk-basic';
                description = 'Основное использование SDK';
                break;
            case 'rag':
                endpoint = '/api/v1/examples/sdk-rag';
                description = 'RAG поиск через SDK';
                break;
            case 'batch':
                endpoint = '/api/v1/examples/sdk-batch';
                description = 'Пакетная генерация через SDK';
                break;
            case 'models':
                endpoint = '/api/v1/examples/sdk-models';
                description = 'Работа с моделями через SDK';
                break;
            default:
                throw new Error('Неизвестный тип примера');
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        
        if (data.success) {
            outputDiv.innerHTML = `
                <div class="mb-2"><strong>${description}</strong></div>
                <div class="mb-2"><small class="text-muted">Время выполнения: ${data.execution_time || 'N/A'}</small></div>
                <pre class="mb-0">${data.output || data.result || 'Пример выполнен успешно'}</pre>
            `;
            statusDiv.innerHTML = '<div class="text-success"><i class="bi bi-check-circle"></i> Выполнено успешно</div>';
        } else {
            outputDiv.innerHTML = `
                <div class="text-danger">
                    <strong>Ошибка выполнения примера:</strong><br>
                    <pre>${data.error || 'Неизвестная ошибка'}</pre>
                </div>
            `;
            statusDiv.innerHTML = '<div class="text-danger"><i class="bi bi-x-circle"></i> Ошибка выполнения</div>';
        }
    } catch (error) {
        outputDiv.innerHTML = `
            <div class="text-danger">
                <strong>Ошибка подключения:</strong><br>
                <pre>${error.message}</pre>
            </div>
        `;
        statusDiv.innerHTML = '<div class="text-danger"><i class="bi bi-x-circle"></i> Ошибка подключения</div>';
    }
}

// Функции для RAG вкладки
async function refreshRAGStatus() {
    try {
        const response = await fetch(`${API_BASE}/rag/status`);
        const data = await response.json();

        const statusDiv = document.getElementById('rag-status');
        const statsDiv = document.getElementById('rag-stats');
        
        if (data.success) {
            statusDiv.innerHTML = `
                <div class="row">
                    <div class="col-6">
                        <strong>Status:</strong><br>
                        <span class="badge ${data.enabled ? 'bg-success' : 'bg-secondary'}">${data.enabled ? 'Enabled' : 'Disabled'}</span>
                    </div>
                    <div class="col-6">
                        <strong>Documents:</strong><br>
                        <span class="badge bg-info">${data.total_chunks || 0}</span>
                    </div>
                </div>
            `;
            
            statsDiv.innerHTML = `
                <div class="mb-2">
                    <small>Index Directory:</small><br>
                    <code>${data.index_dir || './rag_index'}</code>
                </div>
                <div class="mb-2">
                    <small>Total Chunks:</small> <strong>${data.total_chunks || 0}</strong>
                </div>
                <div>
                    <small>Model:</small><br>
                    <code>${data.model || 'sentence-transformers/all-MiniLM-L6-v2'}</code>
                </div>
            `;
            
            // Загружаем значения в поля формы
            document.getElementById('rag-enabled').checked = data.enabled || false;
            document.getElementById('rag-index-dir').value = data.index_dir || './rag_index';
            document.getElementById('rag-model').value = data.model || 'sentence-transformers/all-MiniLM-L6-v2';
            document.getElementById('rag-chunk-size').value = data.chunk_size || 1000;
            document.getElementById('rag-top-k').value = data.top_k || 5;
        } else {
            statusDiv.innerHTML = '<div class="text-danger">Error loading RAG status</div>';
        }
    } catch (error) {
        document.getElementById('rag-status').innerHTML = '<div class="text-danger">Connection error</div>';
    }
}

async function saveRAGConfig() {
    const config = {
        enabled: document.getElementById('rag-enabled').checked,
        index_dir: document.getElementById('rag-index-dir').value || './rag_index',
        model: document.getElementById('rag-model').value || 'sentence-transformers/all-MiniLM-L6-v2',
        chunk_size: parseInt(document.getElementById('rag-chunk-size').value) || 1000,
        top_k: parseInt(document.getElementById('rag-top-k').value) || 5
    };

    try {
        const response = await fetch(`${API_BASE}/rag/config`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(config)
        });
        
        const data = await response.json();
        if (data.success) {
            showAlert('RAG configuration saved successfully', 'success');
            refreshRAGStatus();
        } else {
            showAlert(`Error: ${data.error}`, 'danger');
        }
    } catch (error) {
        showAlert('Error saving RAG config', 'danger');
        console.error('RAG config save error:', error);
    }
}

async function rebuildRAGIndex() {
    try {
        showAlert('Rebuilding RAG index...', 'info');
        const response = await fetch(`${API_BASE}/rag/rebuild`, {
            method: 'POST'
        });

        const data = await response.json();
        if (data.success) {
            showAlert('RAG index rebuilt successfully', 'success');
            refreshRAGStatus();
        } else {
            showAlert(`Error: ${data.error}`, 'danger');
        }
    } catch (error) {
        showAlert('Error rebuilding RAG index', 'danger');
    }
}

async function testRAGSearch() {
    const query = prompt('Enter search query:', 'FastAPI configuration');
    if (!query) return;

    try {
        const response = await fetch(`${API_BASE}/rag/search`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query, top_k: 3})
        });
        
        const data = await response.json();
        const resultsDiv = document.getElementById('rag-test-results');
        const outputDiv = document.getElementById('rag-search-output');
        
        if (data.success && data.results) {
            outputDiv.innerHTML = data.results.map((result, i) => `
                <div class="mb-2 p-2 border-bottom">
                    <strong>Result ${i + 1}:</strong> (Score: ${result.score?.toFixed(3) || 'N/A'})<br>
                    <small class="text-muted">${result.content?.substring(0, 200)}...</small>
                </div>
            `).join('');
            resultsDiv.style.display = 'block';
        } else {
            outputDiv.innerHTML = '<div class="text-muted">No results found</div>';
            resultsDiv.style.display = 'block';
        }
    } catch (error) {
        showAlert('Error testing RAG search', 'danger');
    }
}
// Очистка RAG chunks (оставляем для совместимости)
async function clearRAGChunks() {
    if (!confirm('Вы уверены, что хотите удалить все индексированные документы из RAG системы?\n\nЭто действие нельзя отменить.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/rag/clear`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message || 'RAG chunks успешно очищены', 'success');
            // Обновляем статус если находимся на RAG вкладке
            if (document.getElementById('rag-tab').classList.contains('active')) {
                setTimeout(refreshRAGStatus, 1000);
            }
        } else {
            showAlert(`Ошибка: ${data.error}`, 'danger');
        }
    } catch (error) {
        showAlert('Ошибка очистки RAG chunks', 'danger');
        console.error('Clear RAG chunks error:', error);
    }
}
// Обработка переключения RAG в Settings
function handleRAGToggle(checkbox) {
    // Предотвращаем множественные вызовы
    if (checkbox.disabled) return;

    checkbox.disabled = true;
    setTimeout(() => {
        checkbox.disabled = false;
    }, 2000);
    
    if (checkbox.checked) {
        showAlert('RAG System enabled. Save configuration to apply changes.', 'info');
    } else {
        showAlert('RAG System disabled. Save configuration to apply changes.', 'warning');
    }
}
// Экспорт конфигурации в JSON-файл
async function exportConfig() {
    try {
        const response = await fetch(`${API_BASE}/config/export`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const filename = `fastapi-foundry-config-backup-${timestamp}.json`;

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);

        showAlert(`Конфигурация экспортирована: ${filename}`, 'success');
    } catch (error) {
        showAlert(`Ошибка экспорта: ${error.message}`, 'danger');
    }
}

// Импорт конфигурации из JSON-файл
async function importConfig(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Сбрасываем input чтобы можно было загрузить тот же файл повторно
    event.target.value = '';

    try {
        const text = await file.text();
        const parsed = JSON.parse(text);

        const merge = confirm(
            `Импорт файла: ${file.name}\n\n` +
            `Нажмите OK — слияние с текущей конфигурацией\n` +
            `Нажмите Отмена — полная замена конфигурации`
        );

        const response = await fetch(`${API_BASE}/config/import`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config: parsed, merge })
        });

        const result = await response.json();

        if (result.success) {
            showAlert(
                `Конфигурация импортирована. Разделы: ${result.sections_imported.join(', ')}`,
                'success'
            );
            loadConfigFields();
        } else {
            showAlert(`Ошибка импорта: ${result.detail || result.error}`, 'danger');
        }
    } catch (error) {
        showAlert(`Ошибка чтения файла: ${error.message}`, 'danger');
    }
}

// Удаление модели
async function removeModel(modelId) {
    if (!confirm(`Remove model ${modelId}?\n\nThis will unload the model from memory.`)) {
        return;
    }

    try {
        showAlert(`Removing model ${modelId}...`, 'info');
        
        const response = await fetch(`${API_BASE}/foundry/models/unload`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({model_id: modelId})
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(`Model ${modelId} removed successfully`, 'success');
            loadConnectedModels(); // Refresh models list
        } else {
            showAlert(`Error removing model: ${data.error}`, 'danger');
        }
    } catch (error) {
        showAlert(`Error removing model: ${error.message}`, 'danger');
    }
}