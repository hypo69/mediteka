with open('plugins/web_search/playwright_searcher.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '''        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        extracted_data = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                # Отключаем проверку SSL сертификатов
                context = await browser.new_context(ignore_https_errors=True)
                page = await context.new_page()
                
                # 1. Поиск в DuckDuckGo
                logger.info(f"[playwright_searcher] Загрузка результатов поиска DuckDuckGo...")
                await page.goto(search_url, timeout=20000)
                html = await page.content()
                
                # Парсинг результатов поиска
                soup = BeautifulSoup(html, "html.parser")
                results = []
                for a in soup.find_all("a", class_="result__url"):
                    href = a.get("href")
                    if href:
                        # Извлечение реального URL из DDG редиректа, если нужно
                        # Обычно в HTML версии ссылка прямая или простая
                        parsed_url = urllib.parse.urlparse(href)
                        if parsed_url.netloc == "duckduckgo.com" and "uddg=" in parsed_url.query:
                            qs = urllib.parse.parse_qs(parsed_url.query)
                            real_url = qs.get("uddg", [None])[0]
                            if real_url:
                                results.append(real_url)
                        else:
                            results.append(href)'''

new_block = '''        extracted_data = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                # Отключаем проверку SSL сертификатов
                context = await browser.new_context(ignore_https_errors=True)
                page = await context.new_page()
                
                # 1. Поиск в DuckDuckGo Lite
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

new_content = content.replace(old_block, new_block)
if old_block in content:
    with open('plugins/web_search/playwright_searcher.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('REPLACED OK')
else:
    print('BLOCK NOT FOUND')
