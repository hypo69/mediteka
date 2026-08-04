/**
 * popup.js — AI Recommender popup logic
 *
 * Shows browsing stats and fetches AI recommendations from the server.
 */

const DEFAULT_SERVER = 'http://localhost:9696';

async function getStorage(keys) {
    return chrome.storage.local.get(keys);
}

async function init() {
    const stored = await getStorage(['user_id', 'server_url']);
    const userId = stored.user_id || '—';
    const serverUrl = stored.server_url || DEFAULT_SERVER;

    document.getElementById('server-url').value = serverUrl;

    // Show history count
    try {
        const res = await fetch(`${serverUrl}/api/v1/recommender/history?user_id=${userId}`);
        const data = await res.json();
        document.getElementById('status').textContent =
            `User: ${userId} | Pages tracked: ${data.count ?? 0}`;
    } catch {
        document.getElementById('status').textContent = `Server offline | User: ${userId}`;
    }
}

document.getElementById('save-btn').addEventListener('click', async () => {
    const url = document.getElementById('server-url').value.trim();
    await chrome.storage.local.set({ server_url: url });
    document.getElementById('status').textContent = 'Server URL saved ✓';
});

document.getElementById('recommend-btn').addEventListener('click', async () => {
    const btn = document.getElementById('recommend-btn');
    const resultEl = document.getElementById('result');
    btn.disabled = true;
    btn.textContent = 'Loading…';
    resultEl.textContent = '';

    const stored = await getStorage(['user_id', 'server_url']);
    const userId = stored.user_id;
    const serverUrl = stored.server_url || DEFAULT_SERVER;

    if (!userId) {
        resultEl.textContent = 'No browsing history yet. Visit some pages first.';
        btn.disabled = false;
        btn.textContent = 'Get Recommendations';
        return;
    }

    try {
        const res = await fetch(`${serverUrl}/api/v1/recommender/recommendations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, top_k: 5 }),
        });
        const data = await res.json();
        resultEl.textContent = data.success
            ? data.answer
            : `Error: ${data.error}`;
    } catch (err) {
        resultEl.textContent = `Connection error: ${err.message}`;
    }

    btn.disabled = false;
    btn.textContent = 'Get Recommendations';
});

init();
