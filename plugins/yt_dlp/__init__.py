# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Плагин yt-dlp
# =============================================================================
# Описание:
#   Плагин для скачивания видео и аудио с YouTube и других платформ
#   через библиотеку yt-dlp. Поддерживает:
#     - скачивание видео по URL
#     - скачивание только аудио (mp3) по URL
#     - получение информации о видео без скачивания
#     - поиск видео на YouTube по тексту запроса
#
# Ключевые слова для активации:
#   скачай, скачать, загрузи, загрузить, youtube, youtu.be, yt-dlp,
#   видео с, аудио с, mp3 из, вытащи аудио
#
# File: __init__.py
# Project: mediteka
# Package: plugins.yt_dlp
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
from __future__ import annotations

import asyncio
import re
from pathlib import Path

from plugins.plugin import BasePlugin
from src.logger import logger
from .yt_dlp_client import YtDlpClient

_CFG_FILE = Path(__file__).parent / "config.json"


def _load_cfg():
    from src.utils.jjson import j_loads_ns
    return j_loads_ns(_CFG_FILE)


# Ключевые слова, на которые реагирует плагин
_DOWNLOAD_KEYWORDS = [
    "скачай", "скачать", "загрузи", "загрузить",
    "youtube", "youtu.be", "yt-dlp", "ютуб",
    "видео с", "аудио с", "mp3 из", "вытащи аудио",
    "download video", "download audio",
]

_INFO_KEYWORDS = [
    "информация о видео", "инфо о видео", "что за видео",
    "сколько длится", "video info",
]

_SEARCH_KEYWORDS = [
    "найди видео", "поищи видео", "найди на ютубе",
    "поищи на youtube", "search youtube", "youtube поиск",
]

_AUDIO_KEYWORDS = [
    "аудио", "mp3", "только звук", "музыку", "soundtrack",
    "audio only", "вытащи аудио", "извлеки звук",
]


class YtDlpPlugin(BasePlugin):
    """Плагин скачивания видео и аудио через yt-dlp."""

    name = "yt_dlp"
    title = "Загрузчик видео и аудио yt-dlp"
    description = "Поиск, получение информации и скачивание видео/аудио из YouTube и медиа-платформ"
    icon = "📥"
    version = "2.0.0"
    category = "tools"

    def __init__(self, ai_model) -> None:
        super().__init__(ai_model)
        cfg = _load_cfg()
        self.client = YtDlpClient(cfg)

    def get_manifest(self) -> dict:
        return {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'icon': self.icon,
            'version': self.version,
            'category': self.category,
            'enabled': self.enabled,
            'config': self.get_config(),
            'fields': [
                {
                    'id': 'format',
                    'label': 'Качество видео по умолчанию',
                    'type': 'select',
                    'default': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'options': [
                        {'value': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'label': 'Наилучшее качество (MP4)'},
                        {'value': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]', 'label': 'Full HD 1080p'},
                        {'value': 'bestvideo[height<=720]+bestaudio/best[height<=720]', 'label': 'HD 720p'}
                    ],
                    'description': 'Селектор форматов и качества для скачивания'
                }
            ],
            'actions': []
        }

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def can_handle(self, message: str) -> bool:
        low = message.lower()
        all_keywords = _DOWNLOAD_KEYWORDS + _INFO_KEYWORDS + _SEARCH_KEYWORDS
        has_keyword = any(kw in low for kw in all_keywords)
        has_url = YtDlpClient.is_url(message)
        return has_keyword or has_url

    def _detect_intent(self, message: str) -> str:
        """Определяет намерение: download_video | download_audio | info | search."""
        low = message.lower()
        has_url = YtDlpClient.is_url(message)

        if any(kw in low for kw in _INFO_KEYWORDS):
            return "info"
        if any(kw in low for kw in _SEARCH_KEYWORDS):
            return "search"
        if any(kw in low for kw in _AUDIO_KEYWORDS) and (
            has_url or any(kw in low for kw in _DOWNLOAD_KEYWORDS)
        ):
            return "download_audio"
        if has_url or any(kw in low for kw in _DOWNLOAD_KEYWORDS):
            return "download_video"
        return "search"

    @staticmethod
    def _extract_url(message: str) -> str | None:
        """Извлекает первый URL из сообщения."""
        m = re.search(r"https?://\S+", message)
        return m.group(0).rstrip(".,)") if m else None

    @staticmethod
    def _extract_query(message: str) -> str:
        """Очищает сообщение от ключевых слов для получения поискового запроса."""
        for kw in _SEARCH_KEYWORDS + _DOWNLOAD_KEYWORDS + _AUDIO_KEYWORDS:
            message = message.lower().replace(kw, "")
        return message.strip(" ,.:")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    async def _handle(self, message: str, **kwargs):  # noqa: D401
        intent = self._detect_intent(message)

        if intent == "search":
            async for chunk in self._handle_search(message):
                yield chunk
        elif intent == "info":
            async for chunk in self._handle_info(message):
                yield chunk
        elif intent == "download_audio":
            async for chunk in self._handle_download(message, audio_only=True):
                yield chunk
        else:
            async for chunk in self._handle_download(message, audio_only=False):
                yield chunk

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def _handle_search(self, message: str):
        query = self._extract_query(message)
        if not query:
            yield {"text": "Укажи, что искать на YouTube."}
            return

        yield {"status": f"🔍 Ищу на YouTube: «{query}»..."}

        results = await asyncio.to_thread(self.client.search_youtube, query, 5)
        if not results:
            yield {"text": "Ничего не найдено по вашему запросу."}
            return

        # Уточняем через AI, какой результат наиболее релевантен
        numbered = "\n".join(
            f"{i+1}. {r.get('title', '—')} [{self.client.format_duration(r.get('duration'))}]"
            for i, r in enumerate(results)
        )
        prompt = (
            f"Пользователь искал: \"{message}\"\n"
            f"Найдены следующие видео на YouTube:\n{numbered}\n\n"
            "Кратко прокомментируй каждый результат (1–2 предложения), "
            "отметь наиболее подходящий для запроса пользователя. Ответ на русском."
        )
        yield {"status": "🤖 Анализирую результаты..."}
        ai_comment = await self.ai.ask(prompt) or ""

        yield {"text": self._render_search_html(results, ai_comment)}

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    async def _handle_info(self, message: str):
        url = self._extract_url(message)
        if not url:
            yield {"text": "Не нашёл URL в сообщении. Пришли ссылку на видео."}
            return

        yield {"status": f"📋 Получаю информацию о видео..."}

        info = await asyncio.to_thread(self.client.get_info, url)
        if not info:
            yield {"text": "Не удалось получить информацию о видео. Проверь ссылку."}
            return

        yield {"text": self._render_info_html(info, url)}

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    async def _handle_download(self, message: str, audio_only: bool):
        url = self._extract_url(message)
        if not url:
            yield {"text": "Не нашёл URL в сообщении. Пришли ссылку на видео."}
            return

        media_type = "аудио" if audio_only else "видео"
        yield {"status": f"⬇️ Скачиваю {media_type}..."}

        # Сначала получаем метаданные для отображения названия
        info = await asyncio.to_thread(self.client.get_info, url)
        title = info.get("title", url) if info else url
        yield {"status": f"⬇️ Скачиваю: «{title}»..."}

        progress_state: dict = {"percent": "0%", "speed": "", "eta": ""}

        def _progress_hook(d: dict):
            if d.get("status") == "downloading":
                progress_state["percent"] = d.get("_percent_str", "").strip()
                progress_state["speed"] = d.get("_speed_str", "").strip()
                progress_state["eta"] = d.get("_eta_str", "").strip()

        if audio_only:
            path = await asyncio.to_thread(
                self.client.download_audio, url, _progress_hook
            )
        else:
            path = await asyncio.to_thread(
                self.client.download_video, url, _progress_hook
            )

        if not path or not Path(path).exists():
            yield {"text": f"❌ Не удалось скачать {media_type}. Проверь ссылку или настройки плагина."}
            return

        size_str = self.client.format_filesize(Path(path).stat().st_size)
        yield {"text": self._render_download_html(title, path, size_str, audio_only, info, url)}

    # ------------------------------------------------------------------
    # HTML Renderers
    # ------------------------------------------------------------------

    @staticmethod
    def _render_search_html(results: list[dict], ai_comment: str) -> str:
        cards = []
        for r in results:
            url = r.get("url") or r.get("webpage_url") or f"https://www.youtube.com/watch?v={r.get('id', '')}"
            video_id = ""
            if "watch?v=" in url:
                video_id = url.split("watch?v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]
            else:
                video_id = r.get("id", "")

            title = r.get("title", "—")
            duration = YtDlpClient.format_duration(r.get("duration"))
            uploader = r.get("uploader") or r.get("channel", "")
            thumb = r.get("thumbnail") or r.get("thumbnails", [{}])[-1].get("url", "")
            if not thumb and video_id:
                thumb = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"

            card = (
                f'<div style="border:1px solid rgba(88,166,255,0.2);border-radius:8px;padding:10px;margin:8px 0;display:flex;gap:12px;background:rgba(88,166,255,0.02);align-items:center;">'
                f'  {"<a href=" + repr(url) + " target=\"_blank\"><img src=" + repr(thumb) + " style=\"width:120px;height:68px;object-fit:cover;border-radius:4px;\" /></a>" if thumb else ""}'
                f'  <div>'
                f'    <a href="{url}" target="_blank" style="font-weight:bold;text-decoration:none;color:#58a6ff;">{title}</a><br/>'
                f'    <span style="color:#8b949e;font-size:0.85em;">{uploader} · {duration}</span><br/>'
                f'    <a href="{url}" target="_blank" style="font-size:0.8em;color:#c9d1d9;">{url}</a>'
                f'  </div>'
                f'</div>'
            )
            cards.append(card)

        return (
            '<div>'
            + "".join(cards)
            + (f'<div style="margin-top:12px;padding:10px;background:rgba(255,255,255,0.05);border-radius:6px;border-left:4px solid #58a6ff;">'
               f'<b>Комментарий AI:</b><br/>{ai_comment}</div>' if ai_comment else "")
            + '</div>'
        )

    @staticmethod
    def _render_info_html(info: dict, url: str) -> str:
        title = info.get("title", "—")
        uploader = info.get("uploader") or info.get("channel", "—")
        duration = YtDlpClient.format_duration(info.get("duration"))
        view_count = f"{info.get('view_count', 0):,}".replace(",", " ") if info.get("view_count") else "—"
        like_count = f"{info.get('like_count', 0):,}".replace(",", " ") if info.get("like_count") else "—"
        upload_date_raw = info.get("upload_date", "")
        upload_date = (
            f"{upload_date_raw[:4]}-{upload_date_raw[4:6]}-{upload_date_raw[6:]}"
            if len(upload_date_raw) == 8 else upload_date_raw
        )
        description = (info.get("description") or "")[:300]
        if len(info.get("description") or "") > 300:
            description += "..."
        thumb = info.get("thumbnail", "")
        webpage_url = info.get("webpage_url", url)

        # Форматы: собираем уникальные разрешения
        formats = info.get("formats", [])
        resolutions = sorted(
            {f.get("height") for f in formats if f.get("height")},
            reverse=True,
        )
        res_str = ", ".join(f"{r}p" for r in resolutions[:6]) if resolutions else "—"

        return (
            f'<div style="border:1px solid #ddd;border-radius:8px;padding:14px;">'
            f'  {"<img src=" + repr(thumb) + " style=\"width:100%;max-width:480px;border-radius:6px;margin-bottom:10px;\" /><br/>" if thumb else ""}'
            f'  <h3 style="margin:0 0 6px 0;"><a href="{webpage_url}" target="_blank">{title}</a></h3>'
            f'  <table style="border-collapse:collapse;font-size:0.9em;">'
            f'    <tr><td style="padding:2px 12px 2px 0;color:#666;">Автор</td><td>{uploader}</td></tr>'
            f'    <tr><td style="padding:2px 12px 2px 0;color:#666;">Длительность</td><td>{duration}</td></tr>'
            f'    <tr><td style="padding:2px 12px 2px 0;color:#666;">Просмотры</td><td>{view_count}</td></tr>'
            f'    <tr><td style="padding:2px 12px 2px 0;color:#666;">Лайки</td><td>{like_count}</td></tr>'
            f'    <tr><td style="padding:2px 12px 2px 0;color:#666;">Дата загрузки</td><td>{upload_date}</td></tr>'
            f'    <tr><td style="padding:2px 12px 2px 0;color:#666;">Доступные форматы</td><td>{res_str}</td></tr>'
            f'  </table>'
            f'  {"<p style=\"margin-top:8px;font-size:0.85em;color:#555;\">" + description + "</p>" if description else ""}'
            f'</div>'
        )

    @staticmethod
    def _render_download_html(
        title: str,
        path: Path,
        size_str: str,
        audio_only: bool,
        info: dict | None,
        url: str,
    ) -> str:
        icon = "🎵" if audio_only else "🎬"
        file_name = Path(path).name
        duration = YtDlpClient.format_duration(info.get("duration") if info else None)
        uploader = (info.get("uploader") or info.get("channel", "")) if info else ""
        thumb = (info.get("thumbnail", "")) if info else ""

        return (
            f'<div style="border:1px solid #4caf50;border-radius:8px;padding:14px;">'
            f'  <div style="display:flex;gap:12px;align-items:flex-start;">'
            f'    {"<img src=" + repr(thumb) + " style=\"width:120px;height:68px;object-fit:cover;border-radius:4px;\" />" if thumb else ""}'
            f'    <div>'
            f'      <div style="font-size:1.1em;font-weight:bold;">{icon} {title}</div>'
            f'      {"<div style=\"color:#666;font-size:0.85em;\">" + uploader + " · " + duration + "</div>" if uploader else ""}'
            f'    </div>'
            f'  </div>'
            f'  <hr style="margin:10px 0;border-color:#eee;"/>'
            f'  <div style="font-size:0.9em;">'
            f'    <b>✅ Скачано успешно</b><br/>'
            f'    📁 <code>{file_name}</code><br/>'
            f'    💾 Размер: {size_str}'
            f'  </div>'
            f'</div>'
        )


plugin = YtDlpPlugin
