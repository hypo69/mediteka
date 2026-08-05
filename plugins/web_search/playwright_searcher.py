# -*- coding: utf-8 -*-
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from src.logger import logger

class PlaywrightWebSearcher:
    """Инструмент для поиска информации в интернете с помощью Playwright.
    Использует DuckDuckGo HTML и переходит по ссылкам для извлечения контента.
    """

    async def search_and_extract(self, query: str, num_links: int = 2) -> str:
        """Выполняет поиск по запросу и извлекает текстовое содержимое страниц."""
        logger.info(f"[playwright_searcher] Инициализация поиска: '{query}'")
        
        encoded_query = urllib.parse.quote_plus(query)
        extracted_data = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                # Отключаем проверку SSL сертификатов
                context = await browser.new_context(ignore_https_errors=True)
                page = await context.new_page()
                
                # 1. Поиск в DuckDuckGo Lite (через urllib для надежности)
                logger.info(f"[playwright_searcher] Загрузка результатов поиска DuckDuckGo Lite...")
                
                import urllib.request as urllib_req
                
                url = 'https://lite.duckduckgo.com/lite/'
                data = urllib.parse.urlencode({'q': query}).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                results = []
                
                try:
                    import asyncio
                    # Выполняем синхронный urllib запрос в отдельном потоке
                    def fetch_ddg():
                        with urllib_req.urlopen(req, timeout=10) as response:
                            return response.read().decode('utf-8', errors='ignore')
                            
                    html = await asyncio.to_thread(fetch_ddg)
                    soup = BeautifulSoup(html, "html.parser")
                    for a in soup.find_all("a"):
                        href = a.get("href")
                        if href and href.startswith("http") and "duckduckgo.com" not in href:
                            results.append(href)
                except Exception as e:
                    logger.error(f"[playwright_searcher] Ошибка поиска DDG: {e}")
                            
                # Фильтруем уникальные ссылки
                unique_links = []
                for link in results:
                    if link not in unique_links and not any(x in link for x in ["duckduckgo.com", "yandex.ru", "google.com"]):
                        unique_links.append(link)
                        if len(unique_links) >= num_links:
                            break
                
                logger.info(f"[playwright_searcher] Найдено {len(unique_links)} релевантных ссылок для обхода")
                
                # 2. Обход страниц и извлечение контента
                for link in unique_links:
                    logger.info(f"[playwright_searcher] Загрузка страницы: {link}")
                    try:
                        # Открываем новую вкладку
                        link_page = await context.new_page()
                        await link_page.goto(link, timeout=15000, wait_until="domcontentloaded")
                        
                        # Даем время на дозагрузку JS контента
                        await asyncio.sleep(2)
                        
                        link_html = await link_page.content()
                        await link_page.close()
                        
                        link_soup = BeautifulSoup(link_html, "html.parser")
                        
                        # Очищаем от мусора (скрипты, стили)
                        for s in link_soup(["script", "style", "nav", "footer", "header"]):
                            s.decompose()
                            
                        # Собираем текст из абзацев
                        paragraphs = [p.get_text().strip() for p in link_soup.find_all(["p", "article", "h1", "h2", "h3"])]
                        text_content = "\n".join([p for p in paragraphs if len(p) > 20])
                        
                        # Ограничиваем длину контента страницы (~1500 слов / 8000 символов)
                        text_content = text_content[:8000]
                        
                        if text_content.strip():
                            extracted_data.append({
                                "url": link,
                                "content": text_content
                            })
                            logger.info(f"[playwright_searcher] Успешно извлечено {len(text_content)} симв. со страницы {link}")
                    except Exception as page_ex:
                        logger.error(f"[playwright_searcher] Ошибка при чтении страницы {link}: {page_ex}")
                
                await browser.close()
                
        except Exception as e:
            logger.error(f"[playwright_searcher] Глобальная ошибка поиска Playwright: {e}")
            
        # Формируем итоговый текстовый блок контекста
        if not extracted_data:
            return "Не удалось найти или извлечь информацию из внешних источников в интернете."
            
        formatted_context = "=== НАЙДЕННАЯ ИНФОРМАЦИЯ ИЗ ИНТЕРНЕТА ===\n\n"
        for idx, item in enumerate(extracted_data, 1):
            formatted_context += f"Источник {idx}: {item['url']}\n"
            formatted_context += f"Содержимое:\n{item['content']}\n\n---\n\n"
            
        return formatted_context
