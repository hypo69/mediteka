/**
 * =============================================================================
 * Название процесса: Компонент интерактивного чата Ai Assistant
 * =============================================================================
 * Описание:
 *   Обеспечение двусторонней связи между пользователем и AI-моделью,
 *   включение обработки асинхронных запросов, локализации интерфейса
 *   и механизмы безопасности (nonce-валидация).
 *
 * Примеры:
 *   const chat = new ChatComponent('chat-root');
 *   chat.init();
 *
 * File: chat_component.js
 * Project: Ai Assistant
 * Module: static.js
 * Class: ChatComponent
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

class ChatComponent {
    /**
     * Инициализация базовых параметров компонента.
     * 
     * ПОЧЕМУ КЛАСС, А НЕ ФУНКЦИЯ:
     *   Использование класса позволяет инкапсулировать состояние чата (историю, 
     *   элементы DOM) и избежать загрязнения глобальной области видимости.
     * 
     * ПОЧЕМУ ОДИН ЭЛЕМЕНТ В КОНСТРУКТОРЕ:
     *   Передача ID контейнера обеспечивает гибкость — компонент можно 
     *   встроить в любое место страницы.
     *
     * @param {string} containerId - ID корневого элемента чата.
     */
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        // Acquisition of security credentials from the global scope
        this.nonce = window.Ai AssistantConfig?.nonce || '';
        this.apiUrl = window.Ai AssistantConfig?.apiUrl || '/api/v1/chat';
    }

    /**
     * ! Запуск инициализации компонента.
     * 
     * Returns:
     *   void
     */
    init() {
        // Validation of the root container existence
        if (!this.container) {
            return;
        }

        this._renderBaseLayout();
        this._setupEventListeners();
    }

    /**
     * ! Отправка сообщения в AI бэкенд.
     * 
     * ПОЧЕМУ ASYNC/AWAIT:
     *   Обеспечение неблокирующего интерфейса во время ожидания ответа от модели.
     * 
     * ПОЧЕМУ NONCE В ЗАГОЛОВКАХ:
     *   Соблюдение правил безопасности проекта (6.1, 6.8) для предотвращения CSRF-атак.
     */
    async sendMessage() {
        const input = this.container.querySelector('.chat-input');
        const text = input.value.trim();

        // Prevention of empty content transmission
        if (!text) {
            return;
        }

        // Immediate UI feedback for the user message
        this._addMessageToHistory(text, 'user');
        input.value = '';

        try {
            // Execution of the asynchronous fetch request
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-WP-Nonce': this.nonce // Security check
                },
                body: JSON.stringify({ prompt: text })
            });

            // Validation of the server response status
            if (!response.ok) {
                throw new Error(i18n('chat.error_network')); // Localization placeholder
            }

            const data = await response.json();
            this._addMessageToHistory(data.reply, 'ai');

        } catch (error) {
            // Processing of communication failures
            this._addMessageToHistory(i18n('chat.error_system'), 'error');
        }
    }

    /**
     * ! Отрисовка базовой разметки чата.
     * 
     * ПОЧЕМУ ТЕМПЛЕЙТНЫЕ СТРОКИ:
     *   Упрощение структуры HTML внутри JS-кода.
     * 
     * ПОЧЕМУ data-i18n:
     *   Соответствие правилу 7.1 для автоматической или ручной локализации.
     */
    _renderBaseLayout() {
        this.container.innerHTML = `
            <div class="chat-wrapper">
                <div class="chat-history"></div>
                <div class="chat-controls">
                    <input type="text" class="chat-input" 
                           placeholder="${i18n('chat.placeholder')}" 
                           data-i18n="chat.placeholder">
                    <button class="chat-send-btn" data-i18n="chat.send">
                        ${i18n('chat.send')}
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * ! Настройка слушателей событий.
     */
    _setupEventListeners() {
        const btn = this.container.querySelector('.chat-send-btn');
        const input = this.container.querySelector('.chat-input');

        // Binding of the click event for the submission button
        btn.addEventListener('click', () => this.sendMessage());

        // Handling of the Enter key press for better UX
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    /**
     * ! Добавление сообщения в историю.
     * 
     * @param {string} text - Текст сообщения.
     * @param {string} type - Тип ('user', 'ai', 'error').
     */
    _addMessageToHistory(text, type) {
        const history = this.container.querySelector('.chat-history');
        
        // Guard clause for the history container existence
        if (!history) {
            return;
        }

        const msgDiv = document.createElement('div');
        msgDiv.className = `message message-${type}`;
        
        // Secure text assignment to prevent XSS injection
        msgDiv.textContent = text; 
        
        history.appendChild(msgDiv);
        history.scrollTop = history.scrollHeight;
    }
}