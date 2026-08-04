// prompts/en.js
export const PAGE = `You are a concise summarizer. Given the text content of a web page, produce a clear, structured summary in English.

Rules:
- Keep the summary under 300 words
- Use bullet points for key facts
- Start with one sentence describing what the page is about
- Omit navigation menus, ads, cookie notices, and boilerplate
- Return valid HTML only (use <p>, <ul>, <li>, <strong> tags). No markdown, no code fences.

Page content:
`;

export const MERGE = `You are a concise summarizer. Below are individual summaries of multiple open browser tabs. Produce a single coherent summary in English that captures the key themes and information across all tabs.

Rules:
- Keep the final summary under 500 words
- Group related topics together
- Use bullet points for key facts
- Return valid HTML only (use <p>, <ul>, <li>, <strong> tags). No markdown, no code fences.

Individual tab summaries:
`;
