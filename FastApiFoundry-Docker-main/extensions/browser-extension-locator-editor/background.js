// background.js

const EDITOR_CONTEXT_MENU_ID = "open-locator-editor";

// Create a context menu item on installation.
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: EDITOR_CONTEXT_MENU_ID,
    title: "Open Locator Editor",
    contexts: ["page"]
  });

  // Open the editor page on the first installation of the extension.
  chrome.runtime.onInstalled.addListener((details) => {
    if (details.reason === 'install') {
      chrome.tabs.create({
        url: chrome.runtime.getURL('editor/editor.html')
      });
    }
  });
});

// Handle clicks on the context menu item.
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === EDITOR_CONTEXT_MENU_ID) {
    chrome.tabs.create({
      url: chrome.runtime.getURL('editor/editor.html')
    });
  }
});