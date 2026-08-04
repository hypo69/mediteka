# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Workspace Agent — Gmail, Calendar, Sheets, Docs
# =============================================================================
# Description:
#   Agent with tools for Google Workspace services.
#   Auth: OAuth2 via credentials.json + token.json (stored locally).
#
#   Setup:
#     1. pip install -r requirements-google.txt
#     2. Create OAuth2 credentials at https://console.cloud.google.com/
#        (Desktop app, scopes: Gmail, Calendar, Sheets, Docs)
#     3. Save as credentials.json in project root
#     4. First run will open browser for auth → token.json saved automatically
#
# File: src/agents/google_agent.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial implementation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import base64
import json
import logging
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Optional imports — graceful degradation if google libs not installed
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    _GOOGLE_AVAILABLE = True
except ImportError:
    _GOOGLE_AVAILABLE = False
    logger.warning("⚠️ google-api-python-client not installed. Run: pip install -r requirements-google.txt")

from .base import BaseAgent, ToolDefinition

# OAuth2 scopes
_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
]

_CREDENTIALS_FILE = Path("credentials.json")
_TOKEN_FILE = Path("token.json")


def _get_google_creds() -> Optional["Credentials"]:
    """Load or refresh OAuth2 credentials.

    Returns:
        Credentials: Valid Google OAuth2 credentials, or None on failure.
    """
    if not _GOOGLE_AVAILABLE:
        return None

    creds: Optional[Credentials] = None

    if _TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_FILE), _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not _CREDENTIALS_FILE.exists():
                logger.error("❌ credentials.json not found. See agent docstring for setup.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(_CREDENTIALS_FILE), _SCOPES)
            creds = flow.run_local_server(port=0)
        _TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return creds


class GoogleAgent(BaseAgent):
    """Agent for Google Workspace: Gmail, Calendar, Sheets, Docs."""

    name = "google"
    description = "Работает с Gmail, Google Calendar, Google Sheets и Google Docs"

    @property
    def tools(self) -> List[ToolDefinition]:
        return [
            # ── Gmail ──────────────────────────────────────────────────────
            ToolDefinition(
                name="gmail_list",
                description="Получить список последних писем из Gmail",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Поисковый запрос Gmail (например: 'is:unread', 'from:boss@company.com')"},
                        "max_results": {"type": "integer", "description": "Максимум писем (по умолчанию 10)", "default": 10},
                    },
                    "required": [],
                },
            ),
            ToolDefinition(
                name="gmail_read",
                description="Прочитать письмо по ID",
                parameters={
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string", "description": "ID письма из gmail_list"},
                    },
                    "required": ["message_id"],
                },
            ),
            ToolDefinition(
                name="gmail_send",
                description="Отправить письмо через Gmail",
                parameters={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Email получателя"},
                        "subject": {"type": "string", "description": "Тема письма"},
                        "body": {"type": "string", "description": "Текст письма"},
                    },
                    "required": ["to", "subject", "body"],
                },
            ),
            # ── Calendar ───────────────────────────────────────────────────
            ToolDefinition(
                name="calendar_list",
                description="Получить список предстоящих событий из Google Calendar",
                parameters={
                    "type": "object",
                    "properties": {
                        "max_results": {"type": "integer", "description": "Максимум событий (по умолчанию 10)", "default": 10},
                        "time_min": {"type": "string", "description": "Начало диапазона ISO8601 (по умолчанию — сейчас)"},
                    },
                    "required": [],
                },
            ),
            ToolDefinition(
                name="calendar_create",
                description="Создать событие в Google Calendar",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Название события"},
                        "start": {"type": "string", "description": "Начало события ISO8601 (например: 2025-12-25T10:00:00)"},
                        "end": {"type": "string", "description": "Конец события ISO8601"},
                        "description": {"type": "string", "description": "Описание события (опционально)"},
                        "attendees": {"type": "array", "items": {"type": "string"}, "description": "Email участников (опционально)"},
                    },
                    "required": ["title", "start", "end"],
                },
            ),
            # ── Sheets ─────────────────────────────────────────────────────
            ToolDefinition(
                name="sheets_read",
                description="Прочитать данные из Google Sheets",
                parameters={
                    "type": "object",
                    "properties": {
                        "spreadsheet_id": {"type": "string", "description": "ID таблицы из URL"},
                        "range": {"type": "string", "description": "Диапазон ячеек (например: 'Sheet1!A1:D10')"},
                    },
                    "required": ["spreadsheet_id", "range"],
                },
            ),
            ToolDefinition(
                name="sheets_write",
                description="Записать данные в Google Sheets",
                parameters={
                    "type": "object",
                    "properties": {
                        "spreadsheet_id": {"type": "string", "description": "ID таблицы из URL"},
                        "range": {"type": "string", "description": "Диапазон ячеек (например: 'Sheet1!A1')"},
                        "values": {"type": "array", "items": {"type": "array"}, "description": "Двумерный массив значений [[row1col1, row1col2], [row2col1, ...]]"},
                    },
                    "required": ["spreadsheet_id", "range", "values"],
                },
            ),
            # ── Docs ───────────────────────────────────────────────────────
            ToolDefinition(
                name="docs_read",
                description="Прочитать содержимое Google Docs документа",
                parameters={
                    "type": "object",
                    "properties": {
                        "document_id": {"type": "string", "description": "ID документа из URL"},
                    },
                    "required": ["document_id"],
                },
            ),
            ToolDefinition(
                name="docs_append",
                description="Добавить текст в конец Google Docs документа",
                parameters={
                    "type": "object",
                    "properties": {
                        "document_id": {"type": "string", "description": "ID документа из URL"},
                        "text": {"type": "string", "description": "Текст для добавления"},
                    },
                    "required": ["document_id", "text"],
                },
            ),
        ]

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Dispatch tool call to the appropriate handler.

        Args:
            name: Tool name.
            arguments: Parsed arguments from model tool_call.

        Returns:
            str: Result string passed back to the model.
        """
        if not _GOOGLE_AVAILABLE:
            return "❌ Google API не установлен. Выполните: pip install -r requirements-google.txt"

        handlers = {
            "gmail_list": self._gmail_list,
            "gmail_read": self._gmail_read,
            "gmail_send": self._gmail_send,
            "calendar_list": self._calendar_list,
            "calendar_create": self._calendar_create,
            "sheets_read": self._sheets_read,
            "sheets_write": self._sheets_write,
            "docs_read": self._docs_read,
            "docs_append": self._docs_append,
        }
        handler = handlers.get(name)
        if not handler:
            return f"❌ Неизвестный инструмент: {name}"

        try:
            return await handler(arguments)
        except Exception as e:
            logger.error(f"❌ GoogleAgent tool '{name}' failed: {e}")
            return f"❌ Ошибка: {e}"

    # ── Gmail ──────────────────────────────────────────────────────────────────

    async def _gmail_list(self, args: Dict) -> str:
        creds = _get_google_creds()
        if not creds:
            return "❌ Не удалось получить Google credentials"

        service = build("gmail", "v1", credentials=creds)
        query = args.get("query", "")
        max_results = int(args.get("max_results", 10))

        result = service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()

        messages = result.get("messages", [])
        if not messages:
            return "Писем не найдено"

        lines = []
        for msg in messages:
            meta = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["Subject", "From", "Date"]
            ).execute()
            headers = {h["name"]: h["value"] for h in meta.get("payload", {}).get("headers", [])}
            lines.append(
                f"ID: {msg['id']}\n"
                f"  От: {headers.get('From', '?')}\n"
                f"  Тема: {headers.get('Subject', '?')}\n"
                f"  Дата: {headers.get('Date', '?')}"
            )
        return "\n\n".join(lines)

    async def _gmail_read(self, args: Dict) -> str:
        creds = _get_google_creds()
        if not creds:
            return "❌ Не удалось получить Google credentials"

        service = build("gmail", "v1", credentials=creds)
        msg = service.users().messages().get(
            userId="me", id=args["message_id"], format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        body = _extract_gmail_body(msg.get("payload", {}))

        return (
            f"От: {headers.get('From', '?')}\n"
            f"Кому: {headers.get('To', '?')}\n"
            f"Тема: {headers.get('Subject', '?')}\n"
            f"Дата: {headers.get('Date', '?')}\n\n"
            f"{body[:3000]}"
        )

    async def _gmail_send(self, args: Dict) -> str:
        creds = _get_google_creds()
        if not creds:
            return "❌ Не удалось получить Google credentials"

        service = build("gmail", "v1", credentials=creds)
        mime = MIMEText(args["body"])
        mime["to"] = args["to"]
        mime["subject"] = args["subject"]
        raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()

        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return f"✅ Письмо отправлено на {args['to']}"

    # ── Calendar ───────────────────────────────────────────────────────────────

    async def _calendar_list(self, args: Dict) -> str:
        from datetime import datetime, timezone

        creds = _get_google_creds()
        if not creds:
            return "❌ Не удалось получить Google credentials"

        service = build("calendar", "v3", credentials=creds)
        time_min = args.get("time_min") or datetime.now(timezone.utc).isoformat()
        max_results = int(args.get("max_results", 10))

        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        if not events:
            return "Предстоящих событий нет"

        lines = []
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date", "?"))
            lines.append(f"• {start} — {e.get('summary', 'Без названия')} (ID: {e['id']})")
        return "\n".join(lines)

    async def _calendar_create(self, args: Dict) -> str:
        creds = _get_google_creds()
        if not creds:
            return "❌ Не удалось получить Google credentials"

        service = build("calendar", "v3", credentials=creds)
        event: Dict[str, Any] = {
            "summary": args["title"],
            "start": {"dateTime": args["start"], "timeZone": "UTC"},
            "end": {"dateTime": args["end"], "timeZone": "UTC"},
        }
        if args.get("description"):
            event["description"] = args["description"]
        if args.get("attendees"):
            event["attendees"] = [{"email": e} for e in args["attendees"]]

        created = service.events().insert(calendarId="primary", body=event).execute()
        return f"✅ Событие создано: {created.get('htmlLink', created['id'])}"

    # ── Sheets ─────────────────────────────────────────────────────────────────

    async def _sheets_read(self, args: Dict) -> str:
        creds = _get_google_creds()
        if not creds:
            return "❌ Не удалось получить Google credentials"

        service = build("sheets", "v4", credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=args["spreadsheet_id"],
            range=args["range"],
        ).execute()

        rows = result.get("values", [])
        if not rows:
            return "Данных нет"

        lines = ["\t".join(str(c) for c in row) for row in rows]
        return "\n".join(lines)

    async def _sheets_write(self, args: Dict) -> str:
        creds = _get_google_creds()
        if not creds:
            return "❌ Не удалось получить Google credentials"

        service = build("sheets", "v4", credentials=creds)
        service.spreadsheets().values().update(
            spreadsheetId=args["spreadsheet_id"],
            range=args["range"],
            valueInputOption="USER_ENTERED",
            body={"values": args["values"]},
        ).execute()
        return f"✅ Данные записаны в {args['range']}"

    # ── Docs ───────────────────────────────────────────────────────────────────

    async def _docs_read(self, args: Dict) -> str:
        creds = _get_google_creds()
        if not creds:
            return "❌ Не удалось получить Google credentials"

        service = build("docs", "v1", credentials=creds)
        doc = service.documents().get(documentId=args["document_id"]).execute()

        text_parts = []
        for block in doc.get("body", {}).get("content", []):
            paragraph = block.get("paragraph")
            if not paragraph:
                continue
            for elem in paragraph.get("elements", []):
                text_run = elem.get("textRun")
                if text_run:
                    text_parts.append(text_run.get("content", ""))

        text = "".join(text_parts)
        return text[:5000] if text else "Документ пустой"

    async def _docs_append(self, args: Dict) -> str:
        creds = _get_google_creds()
        if not creds:
            return "❌ Не удалось получить Google credentials"

        service = build("docs", "v1", credentials=creds)
        # Get current end index
        doc = service.documents().get(documentId=args["document_id"]).execute()
        end_index = doc["body"]["content"][-1]["endIndex"] - 1

        service.documents().batchUpdate(
            documentId=args["document_id"],
            body={
                "requests": [{
                    "insertText": {
                        "location": {"index": end_index},
                        "text": "\n" + args["text"],
                    }
                }]
            },
        ).execute()
        return "✅ Текст добавлен в документ"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _extract_gmail_body(payload: Dict) -> str:
    """Recursively extract plain text body from Gmail message payload.

    Args:
        payload: Gmail message payload dict.

    Returns:
        str: Decoded plain text body.
    """
    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = _extract_gmail_body(part)
        if result:
            return result

    return ""
