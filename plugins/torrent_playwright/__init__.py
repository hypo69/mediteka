import re
import json
import asyncio
from plugins.plugin import BasePlugin
from .playwright_searcher import PlaywrightTorrentSearcher
from src.logger import logger

class TorrentPlaywrightPlugin(BasePlugin):
    name = "torrent_playwright"

    def __init__(self, ai_model):
        super().__init__(ai_model)
        self.searcher = PlaywrightTorrentSearcher(ai_model)

    def can_handle(self, message: str) -> bool:
        msg = message.lower()
        torrent_keywords = ["торрент", "torrent", "скачать", "tracker", "раздач", "qbittorrent"]
        return any(kw in msg for kw in torrent_keywords)

    async def _handle(self, message: str) -> str:
        msg = message.lower()

        # Check if the user is looking for torrents
        if not self.can_handle(message):
            return ""

        # Step 1: Use Gemini to extract search query and params
        extract_prompt = (
            f"Пользователь написал запрос: \"{message}\"\n"
            "Тебе нужно понять, какой фильм, сериал или другой контент он ищет, а также желаемое разрешение и размер.\n"
            "Верни строго JSON-объект (без markdown-оберток ```json ... ```) со следующей структурой:\n"
            "{\n"
            "  \"title\": \"название на русском или английском\",\n"
            "  \"resolution\": \"1080p\" или \"720p\" или \"4k\" или \"any\",\n"
            "  \"size_min_gb\": минимальный размер в ГБ (число или null),\n"
            "  \"size_max_gb\": максимальный размер в ГБ (число или null)\n"
            "}\n"
            "Если пользователь не указал конкретных параметров, пиши \"any\" для resolution и null для размеров."
        )

        try:
            raw_extract = await self.ai.ask(extract_prompt)
            # Clean up potential markdown formatting in response
            cleaned_json = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw_extract).strip()
            params = json.loads(cleaned_json)
        except Exception as e:
            logger.error(f"[torrent_playwright] Failed to parse params with Gemini: {e}. Fallback to regex.")
            # Fallback params
            params = {
                "title": message,
                "resolution": "any",
                "size_min_gb": None,
                "size_max_gb": None
            }

        title = params.get("title") or message
        resolution = params.get("resolution") or "any"
        size_min_gb = params.get("size_min_gb")
        size_max_gb = params.get("size_max_gb")

        logger.info(f"[torrent_playwright] Searching for: '{title}', res={resolution}, size={size_min_gb}-{size_max_gb} GB")

        # Step 2: Search torrents using Playwright
        raw_torrents = await self.searcher.search(title)
        if not raw_torrents:
            return "К сожалению, по вашему запросу ничего не найдено на Rutracker и NNMClub."

        # Step 3: Algorithmic filtering
        filtered_torrents = []
        for t in raw_torrents:
            t_title = t["title"].lower()
            
            # Filter by resolution
            if resolution != "any":
                if resolution == "1080p" and not any(r in t_title for r in ["1080", "fhd", "1080p"]):
                    continue
                if resolution == "720p" and not any(r in t_title for r in ["720", "hd", "720p"]) and "1080" in t_title:
                    continue
                if resolution == "4k" and not any(r in t_title for r in ["4k", "2160", "uhd", "2160p"]):
                    continue

            # Filter by size
            size_gb = t["size_bytes"] / (1024 ** 3)
            if size_min_gb is not None and size_gb < size_min_gb:
                continue
            if size_max_gb is not None and size_gb > size_max_gb:
                continue

            filtered_torrents.append(t)

        if not filtered_torrents:
            return (f"Найдено {len(raw_torrents)} раздач по названию '{title}', "
                    f"но ни одна не подошла под ваши фильтры (разрешение: {resolution}, размер: {size_min_gb}-{size_max_gb} GB).")

        # Keep top 15 by seeders for AI analysis
        top_torrents = filtered_torrents[:15]

        # Step 4: Use Gemini to select, rank and generate clean HTML response
        torrents_data_str = json.dumps([{
            "idx": i + 1,
            "title": t["title"],
            "size_human": t["size_human"],
            "seeds": t["seeds"],
            "peers": t["peers"],
            "source": t["source"],
            "view_url": t["view_url"],
            "download_url": t["download_url"]
        } for i, t in enumerate(top_torrents)], ensure_ascii=False, indent=2)

        ai_prompt = (
            f"Пользователь искал: \"{message}\"\n"
            f"Вот список найденных торрентов (отфильтрованных по его критериям):\n"
            f"{torrents_data_str}\n\n"
            "Пожалуйста, выбери до 7 наиболее качественных и релевантных раздач.\n"
            "Сгруппируй или отсортируй их так, чтобы пользователю было удобно выбрать (например, сначала лучшие 1080p, затем 720p, или по переводам/сезонам).\n"
            "Оформи ответ как стильный HTML-блок. Не используй markdown-блоки ```html ... ```, верни чистый HTML-текст.\n"
            "Для каждого торрента создай аккуратную карточку или элемент списка со структурой:\n"
            "- Название торрента (как ссылка на view_url с target='_blank')\n"
            "- Источник (Rutracker или NNMClub), размер в ГБ, количество сидов и пиров\n"
            "- Краткое пояснение (качество, перевод, или сезон)\n"
            "- Кнопка для добавления в закачку. Код кнопки должен быть строго таким:\n"
            "<button class=\"btn btn-sm btn-outline-success download-torrent-btn mt-2\" "
            "data-url=\"DOWNLOAD_URL\" data-source=\"SOURCE\" data-title=\"CLEAN_TITLE\">"
            "📥 Скачать в qBittorrent</button>\n"
            "Где:\n"
            "- DOWNLOAD_URL - это оригинальный 'download_url' торрента из предоставленного JSON.\n"
            "- SOURCE - это 'source' торрента ('rutracker' или 'nnmclub').\n"
            "- CLEAN_TITLE - это очищенное, понятное название фильма/сериала для отображения в панели статуса.\n\n"
            "Добавь в начале небольшой текст с описанием результатов (какие фильтры применились)."
        )

        try:
            formatted_response = await self.ai.ask(ai_prompt)
            # Remove markdown code blocks if AI ignored instructions
            formatted_response = re.sub(r"```(?:html)?\s*([\s\S]*?)\s*```", r"\1", formatted_response).strip()
            return formatted_response
        except Exception as e:
            logger.error(f"[torrent_playwright] Failed to format response with Gemini: {e}")
            # Fallback plain-text/HTML rendering
            html_lines = ["<h5>Результаты поиска торрентов:</h5><div class='list-group'>"]
            for t in top_torrents[:7]:
                btn_html = (
                    f"<button class='btn btn-sm btn-outline-success download-torrent-btn mt-2' "
                    f"data-url='{t['download_url']}' data-source='{t['source']}' data-title='{t['title'][:40]}'>"
                    f"📥 Скачать в qBittorrent</button>"
                )
                html_lines.append(
                    f"<div class='list-group-item list-group-item-action flex-column align-items-start'>"
                    f"  <div class='d-flex w-100 justify-content-between'>"
                    f"    <h6 class='mb-1'><a href='{t['view_url']}' target='_blank'>{t['title']}</a></h6>"
                    f"    <small class='text-muted'>{t['source'].upper()}</small>"
                    f"  </div>"
                    f"  <p class='mb-1'>Размер: {t['size_human']} | Сиды: {t['seeds']} | Пиры: {t['peers']}</p>"
                    f"  {btn_html}"
                    f"</div>"
                )
            html_lines.append("</div>")
            return "\n".join(html_lines)

plugin = TorrentPlaywrightPlugin
