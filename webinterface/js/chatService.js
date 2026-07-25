// Shared Chat Service Module
// Exposes window.chatService to unify API calling and message/error formatting.

window.chatService = {
  /**
   * Sends a chat message to the /api/chat backend.
   * Resolves to the text reply or throws the parsed error object/string.
   * 
   * @param {string} message 
   * @returns {Promise<any>}
   */
  async sendChatMessage(message, onChunk, history = [], generationConfig = {}) {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history, generation_config: generationConfig })
    });
    
    if (!response.ok) {
      let data;
      try {
        data = await response.json();
      } catch (e) {
        throw new Error(`Ошибка сервера (HTTP ${response.status}): ${response.statusText}`);
      }
      throw (data.detail || data);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let fullText = '';
    let voiceText = '';
    
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();
      
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        if (trimmed.startsWith('data: ')) {
          try {
            const data = JSON.parse(trimmed.substring(6));
            if (data.error) {
              throw new Error(data.error);
            }
            if (data.text || data.status || data.voice) {
              if (data.text) fullText += data.text;
              if (data.voice) voiceText += data.voice;
              if (onChunk) {
                onChunk(data.text || '', data.status || '', data.voice || '');
              }
            }
          } catch (e) {
            console.error('Parsing SSE error:', e, trimmed);
          }
        }
      }
    }
    
    if (buffer && buffer.trim().startsWith('data: ')) {
      try {
        const data = JSON.parse(buffer.trim().substring(6));
        if (data.error) throw new Error(data.error);
        if (data.text || data.status || data.voice) {
          if (data.text) fullText += data.text;
          if (data.voice) voiceText += data.voice;
          if (onChunk) onChunk(data.text || '', data.status || '', data.voice || '');
        }
      } catch (e) {}
    }
    
    return { text: fullText, voice: voiceText };
  },


  /**
   * Formats chat messages. 
   * Converts objects into stringified JSON inside pre tags for rich rendering.
   * 
   * @param {any} text 
   * @returns {string|HTMLElement}
   */
  formatMessage(text) {
    if (typeof text === 'object' && text !== null) {
      return `<pre style="white-space: pre-wrap; background: #2b2b2b; color: #ff7070; padding: 10px; border-radius: 5px; margin: 5px 0; font-family: monospace;">${JSON.stringify(text, null, 2)}</pre>`;
    }
    return text;
  },

  /**
   * Reads the given text aloud using the browser SpeechSynthesis API.
   * 
   * @param {string|object} text 
   */
  async speak(text) {
    if (!text) return;
    
    let cleanText = '';
    if (typeof text === 'object') {
      const title = text.title_ru || text.title;
      const rec = text.why_watch || text.plot || '';
      cleanText = `Найдено: ${title}. ${rec}`;
    } else {
      const trimmed = text.trim();
      if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
        try {
          const card = JSON.parse(trimmed);
          const title = card.title_ru || card.title;
          const rec = card.why_watch || card.plot || '';
          cleanText = `Найдено: ${title}. ${rec}`;
        } catch (e) {
          cleanText = trimmed;
        }
      } else {
        // Strip code blocks
        cleanText = trimmed.replace(/```[\s\S]*?```/g, '');
        // Strip HTML tags
        cleanText = cleanText.replace(/<[^>]*>/g, '');
        // Strip Markdown formatting
        cleanText = cleanText.replace(/[*_`#]/g, '');
      }
    }
    
    if (!cleanText.trim()) return;

    let userSettings = null;
    try {
      const response = await fetch('/auth/settings');
      if (response.ok) {
        userSettings = await response.json();
        if (userSettings.tts_enabled === 1 && userSettings.tts_system && userSettings.tts_system !== 'browser') {
          const queryParams = new URLSearchParams({
            text: cleanText,
            system: userSettings.tts_system,
            voice: userSettings.tts_voice
          });
          const audioUrl = `/api/tts/synthesize?${queryParams.toString()}`;
          if (window.chatServiceAudio) {
            window.chatServiceAudio.pause();
          }
          window.chatServiceAudio = new Audio(audioUrl);
          await window.chatServiceAudio.play();
          return;
        }
      }
    } catch (e) {
      console.error('Failed to speak using backend TTS, falling back to browser:', e);
    }

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.lang = 'ru-RU';
      
      if (userSettings && userSettings.tts_voice) {
        const voices = window.speechSynthesis.getVoices();
        const selectedVoice = voices.find(v => v.name === userSettings.tts_voice);
        if (selectedVoice) {
          utterance.voice = selectedVoice;
        }
      }
      
      window.speechSynthesis.speak(utterance);
    }
  }
};
