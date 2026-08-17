# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Playwright Web Searcher
# =============================================================================
# Описание:
#   Инструмент прямого интернет-поиска через DuckDuckGo Lite с извлечением
#   сниппетов и глубоким сбором текста веб-страниц через Playwright Chromium.
#
# File: playwright_searcher.py
# Package: plugins.web_search
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import urllib.parse
import urllib.request as urllib_req
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from src.logger import logger

# Домены с агрессивной защитой от ботов (Cloudflare/Капча) или страницы видеоплееров
_SKIP_SCRAPE_DOMAINS = {
    'kinopoisk.ru',
    'yandex.ru',
    'google.com',
    'vk.com',
    'vkvideo.ru',
    'rutube.ru',
    'youtube.com',
    'youtu.be',
    'ivi.ru',
    'okko.tv',
    'premier.one',
    'kion.ru',
    'amediateka.ru',
    'duckduckgo.com',
}


class PlaywrightWebSearcher:
    """Инструмент для поиска информации в интернете с помощью Playwright и DuckDuckGo."""

    def _fetch_ddg_results(self, query: str) -> List[Dict[str, str]]:
        """Выполняет поиск в DuckDuckGo Lite и извлекает список результатов со сниппетами."""
        url = 'https://lite.duckduckgo.com/lite/'
        data = urllib.parse.urlencode({'q': query}).encode('utf-8')
        req = urllib_req.Request(
            url,
            data=data,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )

        results: List[Dict[str, str]] = []
        try:
            with urllib_req.urlopen(req, timeout=12) as response:
                html = response.read().decode('utf-8', errors='ignore')

            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', class_='result-link'):
                href = a.get('href', '').strip()
                if not href or not href.startswith('http'):
                    continue

                title = a.get_text().strip()
                snippet = ''
                parent_tr = a.find_parent('tr')
                if parent_tr:
                    next_tr = parent_tr.find_next_sibling('tr')
                    if next_tr:
                        snippet_td = next_tr.find('td', class_='result-snippet')
                        if snippet_td:
                            snippet = snippet_td.get_text().strip()

                results.append({
                    'title': title or href,
                    'url': href,
                    'snippet': snippet,
                })

            # Фолбэк на поиск обычных ссылок, если разметка lite изменилась
            if not results:
                for a in soup.find_all('a'):
                    href = a.get('href', '').strip()
                    if href.startswith('http') and 'duckduckgo.com' not in href:
                        results.append({
                            'title': a.get_text().strip() or href,
                            'url': href,
                            'snippet': '',
                        })

        except Exception as e:
            logger.error(f"[playwright_searcher] Ошибка запроса к DuckDuckGo: {e}")

        return results

    async def search_and_extract(self, query: str, num_links: int = 2) -> str:
        """Выполняет поиск по запросу и извлекает текстовое содержимое страниц.

        Args:
            query: Поисковый запрос.
            num_links: Количество страниц для полного обхода браузером.

        Returns:
            str: Сформированный контекст поиска.
        """
        logger.info(f"[playwright_searcher] Инициализация поиска: '{query}'")

        # 1. Поиск результатов и сниппетов через DuckDuckGo Lite
        ddg_results = await asyncio.to_thread(self._fetch_ddg_results, query)
        if not ddg_results:
            logger.warning(f"[playwright_searcher] Поиск не вернул результатов для: '{query}'")
            return "Не удалось найти информацию по данному запросу в поисковой системе."

        logger.info(f"[playwright_searcher] Найдено {len(ddg_results)} результатов поиска")

        # 2. Выбор ссылок для глубокого сбора контента
        scrape_targets: List[Dict[str, str]] = []
        for item in ddg_results:
            url = item['url']
            domain = urllib.parse.urlparse(url).netloc.lower()
            if any(skip in domain for skip in _SKIP_SCRAPE_DOMAINS):
                continue
            scrape_targets.append(item)
            if len(scrape_targets) >= num_links:
                break

        # 3. Обход страниц через Playwright (если доступны подходящие ссылки)
        crawled_articles: List[Dict[str, str]] = []
        if scrape_targets:
            try:
                from playwright.async_api import async_playwright
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(
                        ignore_https_errors=True,
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    )

                    for target in scrape_targets:
                        link = target['url']
                        logger.info(f"[playwright_searcher] Загрузка страницы: {link}")
                        try:
                            page = await context.new_page()
                            await page.goto(link, timeout=12000, wait_until='domcontentloaded')
                            await asyncio.sleep(1.5)

                            link_html = await page.content()
                            await page.close()

                            link_soup = BeautifulSoup(link_html, 'html.parser')
                            for s in link_soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
                                s.decompose()

                            paragraphs = [p_tag.get_text().strip() for p_tag in link_soup.find_all(['p', 'article', 'h1', 'h2', 'h3', 'section'])]
                            text_content = '\n'.join([p_text for p_text in paragraphs if len(p_text) > 25])
                            text_content = text_content[:7000]

                            if text_content.strip():
                                crawled_articles.append({
                                    'title': target.get('title', link),
                                    'url': link,
                                    'content': text_content
                                })
                                logger.info(f"[playwright_searcher] Извлечено {len(text_content)} симв. со страницы {link}")
                        except Exception as page_ex:
                            logger.warning(f"[playwright_searcher] Не удалось загрузить страницу {link}: {page_ex}")

                    await browser.close()
            except Exception as e:
                logger.error(f"[playwright_searcher] Ошибка браузера Playwright: {e}")

        # 4. Формирование итогового ответа
        parts: List[str] = []

        if crawled_articles:
            parts.append("=== НАЙДЕННЫЕ МАТЕРИАЛЫ СТРАНИЦ ===")
            for idx, art in enumerate(crawled_articles, 1):
                parts.append(f"### {idx}. [{art['title']}]({art['url']})\n{art['content']}\n")

        # Добавляем сниппеты из поисковой выдачи для полноты картины
        parts.append("=== РЕЗУЛЬТАТЫ ПОИСКОВОЙ ВЫДАЧИ ===")
        for idx, res in enumerate(ddg_results[:8], 1):
            snippet_str = f": {res['snippet']}" if res['snippet'] else ""
            parts.append(f"{idx}. **[{res['title']}]({res['url']})**{snippet_str}")

        return "\n\n".join(parts)
