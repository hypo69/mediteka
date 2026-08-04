/**
 * content.js — Page time tracker
 *
 * Measures time spent on the current page and sends a page_view
 * message to the background service worker on page unload.
 */

let _startTime = Date.now();

// Send page_view event to background on unload
window.addEventListener('pagehide', () => {
    const timeSpent = Math.round((Date.now() - _startTime) / 1000);
    if (timeSpent < 3) return; // Ignore accidental navigations

    chrome.runtime.sendMessage({
        type: 'PAGE_VIEW',
        url: location.href,
        title: document.title,
        time_spent: timeSpent,
        timestamp: new Date().toISOString(),
    });
});

// Reset timer on visibility change (tab switch)
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        _startTime = Date.now();
    }
});
