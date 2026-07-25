MCP-like server
================

This folder contains a minimal MCP-like server (Node/Express) that provides two endpoints:

- POST /precommit { message } - stages and commits any current repo changes with the given message
- POST /apply { filePath, content } - writes content to filePath under the repo root

Usage:

1. cd .mcp
2. npm install
3. npm start

Security: This is a minimal local helper and is NOT hardened. Do not expose it publicly.
