## \file plugins/media_layer/media_layer.py
# -*- coding: utf-8 -*-
"""Слой маршрутизации медиа-запросов. Инструкция строится из media.db."""

import json
from pathlib import Path

from plugins.plugin import BasePlugin
from plugins.media_organizer.core.database import MediaDatabase

_DB_FILE = Path(__file__).parent.parent / "media_organizer" / "data" / "media.db"

_MEDIA_KEYWORDS = (
    "фильм", "сериал", "кино", "эпизод", "сезон", "актёр", "режиссёр",
    "movie", "series", "episode", "season", "actor", "director", "film",
    "диск", "медиа", "media", "посмотреть", "рекомендуй", "похожее",
)


def _build_instruction(db: MediaDatabase) -> str:
    records = db.export_all()
    if not records:
        return ""
    return (
        "Ты — медиа-ассистент. Отвечай ТОЛЬКО на основе данных ниже.\n"
        "Если ответа нет в данных — так и скажи.\n\n"
        "=== МЕДИАТЕКА ===\n"
        + json.dumps(records, ensure_ascii=False, indent=2)
    )


class MediaLayerPlugin(BasePlugin):
    name = "media_layer"

    def __init__(self, ai_model):
        super().__init__(ai_model)
        self._instruction = ""
        if _DB_FILE.exists():
            self._instruction = _build_instruction(MediaDatabase(_DB_FILE))

    def _is_media_query(self, message: str) -> bool:
        low = message.lower()
        return any(kw in low for kw in _MEDIA_KEYWORDS)

    def can_handle(self, message: str) -> bool:
        return bool(self._instruction) and self._is_media_query(message)

    async def _handle(self, message: str) -> str | None:
        if not self.can_handle(message):
            return None
        return await self.ai.ask(f"{self._instruction}\n\n=== ВОПРОС ===\n{message}")
