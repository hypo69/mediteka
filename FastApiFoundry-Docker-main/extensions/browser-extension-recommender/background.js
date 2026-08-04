/**
 * background.js — Service worker for AI Recommender extension
 *
 * Receives PAGE_VIEW messages from content.js and forwards them
 * to the AI Assistant server at /api/v1/recommender/track.
 */

const DEFAULT_SERVER = 'http://localhost:9696';

// Generate or retrieve a persistent user_id for this browser profile
async function getUserId() {
    const stored = await chrome.storage.local.get('user_id');
    if (stored.user_id) return stored.user_id;
    const id = 'user_' + Math.random().toString(36).slice(2, 10);
    await chrome.storage.local.set({ user_id: id });
    return id;
}

async function getServerUrl() {
    const stored = await chrome.storage.local.get('server_url');
    return stored.server_url || DEFAULT_SERVER;
}

// Send a page_view event to the server
async function trackPageView(event) {
    const [userId, serverUrl] = await Promise.all([getUserId(), getServerUrl()]);
    try {
        await fetch(`${serverUrl}/api/v1/recommender/track`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, ...event }),
        });
    } catch (err) {
        // Server may be offline — silently ignore
        console.debug('[AI Recommender] track failed:', err.message);
    }
}

chrome.runtime.onMessage.addListener((message) => {
    if (message.type === 'PAGE_VIEW') {
        trackPageView({
            url: message.url,
            title: message.title,
            time_spent: message.time_spent,
            timestamp: message.timestamp,
        });
    }
});
