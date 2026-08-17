import os
import re
import io
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
import PIL.Image
from playwright.async_api import async_playwright
from src.logger import logger

class PlaywrightTorrentSearcher:
    """Searches torrents on Rutracker and NNMClub using Playwright with lazy login."""

    def __init__(self, ai_model=None):
        self.ai = ai_model
        self.rutracker_user = os.getenv("RUTRACKER_USERNAME", "hypo69")
        self.rutracker_pass = os.getenv("RUTRACKER_PASSWORD", "@Davidka#1969")
        self.storage_state_dir = Path(__file__).parent / "session_state"
        self.storage_state_dir.mkdir(parents=True, exist_ok=True)

    def _parse_size(self, size_str: str) -> int:
        """Parses size string (e.g. '14.2 GB', '1.5 ГБ', '700 MB') into bytes."""
        size_str = size_str.replace(",", ".").strip().lower()
        size_str = size_str.replace("гб", "gb").replace("мб", "mb").replace("кб", "kb").replace("б", "b")
        m = re.match(r"([\d.]+)\s*([gmk]?b)", size_str)
        if not m:
            return 0
        val = float(m.group(1))
        unit = m.group(2)
        if unit == "gb":
            return int(val * 1024 * 1024 * 1024)
        elif unit == "mb":
            return int(val * 1024 * 1024)
        elif unit == "kb":
            return int(val * 1024)
        return int(val)

    async def search(self, query: str) -> list[dict]:
        """Runs parallel search on Rutracker and NNMClub."""
        tasks = [
            self.search_nnmclub(query),
            self.search_rutracker(query)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        flat_results = []
        for r in results:
            if isinstance(r, list):
                flat_results.extend(r)
            elif isinstance(r, Exception):
                logger.error(f"[playwright_searcher] Search error: {r}")
                
        # Sort by seeders descending
        flat_results.sort(key=lambda x: x.get("seeds", 0), reverse=True)
        return flat_results

    async def search_rutracker(self, query: str) -> list[dict]:
        """Lazy search on Rutracker.org: tries guest first, logs in only if redirected."""
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context_path = self.storage_state_dir / "rutracker"
            context = await p.chromium.launch_persistent_context(str(context_path), headless=True)
            page = await context.new_page()

            try:
                # 1. Try guest search first
                await page.goto("https://rutracker.org/forum/tracker.php", timeout=20000)
                html = await page.content()
                
                needs_login = "login.php" in page.url or "Выход" not in html
                
                # 2. If redirected to login page, perform login with captcha
                if needs_login:
                    logger.info("[playwright_searcher] Rutracker requires login. Performing lazy authentication...")
                    success = False
                    for attempt in range(4):
                        logger.info(f"[playwright_searcher] Rutracker login attempt {attempt + 1}/4...")
                        await page.goto("https://rutracker.org/forum/login.php", timeout=20000)
                        await page.fill("#login-form-full input[name='login_username']", self.rutracker_user)
                        await page.fill("#login-form-full input[name='login_password']", self.rutracker_pass)
                        
                        captcha_element = page.locator("#login-form-full img[alt='pic']")
                        if await captcha_element.count() > 0 and self.ai:
                            captcha_bytes = await captcha_element.screenshot()
                            image = PIL.Image.open(io.BytesIO(captcha_bytes))
                            
                            captcha_prompt = (
                                "This is a captcha image from a forum. It contains exactly 4 characters (lowercase letters and digits) "
                                "printed on a purple background. There is a dark bar at the bottom with the text 'rutracker.org' - IGNORE it. "
                                "Focus only on the 4 large characters in the middle. Identify them and output ONLY these 4 characters in lowercase, "
                                "without spaces or any other text."
                            )
                            response = self.ai._client.models.generate_content(
                                model=self.ai.model_name,
                                contents=[image, captcha_prompt]
                            )
                            captcha_text = response.text.strip().lower()
                            captcha_text = re.sub(r'[^a-z0-9]', '', captcha_text)[:4]
                            logger.info(f"[playwright_searcher] Gemini solved captcha: '{captcha_text}'")
                            await page.fill("#login-form-full input[name^='cap_code_']", captcha_text)
                        
                        await page.click("#login-form-full input[name='login']")
                        
                        for _ in range(5):
                            await page.wait_for_timeout(1000)
                            html = await page.content()
                            if "Выход" in html:
                                success = True
                                break
                        
                        if success:
                            logger.info("[playwright_searcher] Successfully logged in to Rutracker!")
                            break
                        else:
                            logger.warn("[playwright_searcher] Rutracker login attempt failed. Retrying...")

                    if not success:
                        logger.error("[playwright_searcher] Rutracker login failed after attempts. Skipping.")
                        await context.close()
                        await browser.close()
                        return []

                # 3. Now search
                await page.goto("https://rutracker.org/forum/tracker.php", timeout=20000)
                await page.fill("input[name='nm'] >> visible=true", query)
                await page.click("input[type='submit'][value='поиск'] >> visible=true")
                await page.wait_for_load_state("networkidle")

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                table = soup.find("table", id="tor-tbl")
                if table:
                    rows = table.find_all("tr", class_="tCenter")
                    for row in rows:
                        cells = row.find_all("td")
                        if len(cells) < 10:
                            continue
                        
                        cat_link = cells[2].find("a")
                        category = cat_link.text.strip() if cat_link else ""
                        
                        title_cell = cells[3]
                        title_link = title_cell.find("a", class_="tLink")
                        if not title_link:
                            continue
                        title = title_link.text.strip()
                        view_url = "https://rutracker.org/forum/" + title_link["href"]
                        
                        dl_link = title_cell.find("a", class_="dl-stub")
                        if not dl_link:
                            dl_link = cells[5].find("a", class_="small")
                        download_url = "https://rutracker.org/forum/" + dl_link["href"] if dl_link else ""
                        
                        size_cell = cells[5]
                        size_text = size_cell.text.strip().replace("\xa0", " ")
                        size_bytes = self._parse_size(size_text)
                        
                        seeds_cell = cells[6]
                        seeds_text = seeds_cell.text.strip()
                        seeds = int(seeds_text) if seeds_text.isdigit() else 0
                        
                        leech_cell = cells[7]
                        leech_text = leech_cell.text.strip()
                        leechers = int(leech_text) if leech_text.isdigit() else 0
                        
                        results.append({
                            "title": title,
                            "category": category,
                            "view_url": view_url,
                            "download_url": download_url,
                            "size_bytes": size_bytes,
                            "size_human": size_text,
                            "seeds": seeds,
                            "peers": leechers,
                            "source": "rutracker"
                        })
            except Exception as e:
                logger.error(f"[playwright_searcher] Rutracker search exception: {e}")
            finally:
                await context.close()
                await browser.close()
                
        return results

    async def search_nnmclub(self, query: str) -> list[dict]:
        """Searches NNMClub.to directly as guest."""
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await page.goto("https://nnmclub.to/forum/tracker.php", timeout=20000)
                await page.fill("input[name='nm'] >> visible=true", query)
                await page.click("input[type='submit'][value='Поиск'] >> visible=true")
                await page.wait_for_load_state("networkidle")

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                table = soup.find("table", class_="tablesorter")
                if table:
                    rows = table.find_all("tr", class_=re.compile(r"prow[12]"))
                    for row in rows:
                        cells = row.find_all("td")
                        if len(cells) < 10:
                            continue
                        
                        cat_link = cells[1].find("a")
                        category = cat_link.text.strip() if cat_link else ""
                        
                        title_cell = cells[2]
                        title_link = title_cell.find("a", class_="likeLink") or title_cell.find("a", class_="genmed")
                        if not title_link:
                            continue
                        title = title_link.text.strip()
                        view_url = "https://nnmclub.to/forum/" + title_link["href"]
                        
                        download_url = ""
                        magnet_url = ""
                        links = title_cell.find_all("a")
                        for l in links:
                            href = l.get("href", "")
                            if "download.php" in href:
                                download_url = "https://nnmclub.to/forum/" + href
                            elif href.startswith("magnet:"):
                                magnet_url = href
                                
                        size_cell = cells[5]
                        size_text = size_cell.text.strip().replace("\xa0", " ")
                        size_bytes = self._parse_size(size_text)
                        
                        seeds_cell = cells[6]
                        seeds_text = seeds_cell.text.strip()
                        seeds = int(seeds_text) if seeds_text.isdigit() else 0
                        
                        leech_cell = cells[7]
                        leech_text = leech_cell.text.strip()
                        leechers = int(leech_text) if leech_text.isdigit() else 0
                        
                        results.append({
                            "title": title,
                            "category": category,
                            "view_url": view_url,
                            "download_url": magnet_url or download_url,
                            "size_bytes": size_bytes,
                            "size_human": size_text,
                            "seeds": seeds,
                            "peers": leechers,
                            "source": "nnmclub"
                        })
            except Exception as e:
                logger.error(f"[playwright_searcher] NNMClub search exception: {e}")
            finally:
                await context.close()
                await browser.close()
                
        return results

    async def download_torrent_file(self, source: str, url: str) -> bytes | None:
        """Downloads a .torrent file from Rutracker or NNMClub using persistent context."""
        if not url:
            return None
            
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context_path = self.storage_state_dir / source
            context = await p.chromium.launch_persistent_context(str(context_path), headless=True)
            page = await context.new_page()
            
            try:
                if source == "rutracker":
                    await page.goto("https://rutracker.org/forum/index.php", timeout=15000)
                else:
                    await page.goto("https://nnmclub.to/forum/index.php", timeout=15000)
                    
                async with page.expect_download(timeout=25000) as download_info:
                    await page.goto(url)
                
                download = await download_info.value
                path = await download.path()
                if path:
                    with open(path, "rb") as f:
                        return f.read()
            except Exception as e:
                logger.error(f"[playwright_searcher] Failed to download torrent file: {e}")
            finally:
                await context.close()
                await browser.close()
        return None
