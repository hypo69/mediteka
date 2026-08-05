import re

with open('plugins/web_search/playwright_searcher.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '''                # 1. Поиск в DuckDuckGo Lite
                logger.info(f"[playwright_searcher] Загрузка результатов поиска DuckDuckGo Lite...")
                await page.goto("https://lite.duckduckgo.com/lite/", timeout=20000)
                await page.fill('input[name="q"]', query)
                await page.click('input[type="submit"]')
                await page.wait_for_load_state('networkidle')
                html = await page.content()
                
                # Парсинг результатов поиска
                soup = BeautifulSoup(html, "html.parser")
                results = []
                for a in soup.find_all("a"):
                    href = a.get("href")
                    if href and href.startswith("http") and "duckduckgo.com" not in href:
                        results.append(href)'''

new_block = '''                # 1. Поиск в DuckDuckGo Lite (через urllib для надежности)
                logger.info(f"[playwright_searcher] Загрузка результатов поиска DuckDuckGo Lite...")
                
                import urllib.request
                import urllib.parse
                
                url = 'https://lite.duckduckgo.com/lite/'
                data = urllib.parse.urlencode({'q': query}).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                results = []
                
                try:
                    import asyncio
                    # Выполняем синхронный urllib запрос в отдельном потоке
                    def fetch_ddg():
                        with urllib.request.urlopen(req, timeout=10) as response:
                            return response.read().decode('utf-8', errors='ignore')
                            
                    html = await asyncio.to_thread(fetch_ddg)
                    soup = BeautifulSoup(html, "html.parser")
                    for a in soup.find_all("a"):
                        href = a.get("href")
                        if href and href.startswith("http") and "duckduckgo.com" not in href:
                            results.append(href)
                except Exception as e:
                    logger.error(f"[playwright_searcher] Ошибка поиска DDG: {e}")'''

new_content = content.replace(old_block, new_block)
if old_block in content:
    with open('plugins/web_search/playwright_searcher.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('REPLACED OK')
else:
    print('BLOCK NOT FOUND')
