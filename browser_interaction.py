import asyncio
from playwright.async_api import async_playwright, Playwright, Browser, Page

class BrowserManager:
    """
    Manages browser interactions using Playwright.
    Handles launching browser, opening pages, navigating, and searching.
    """
    def __init__(self):
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None
        self._is_initialized = False

    async def _ensure_initialized(self):
        """Initializes Playwright and launches a persistent browser if not already done."""
        if not self._is_initialized:
            self.playwright = await async_playwright().start()
            # Using chromium, assuming it's installed via `playwright install chrome`
            # For Windows, Edge (msedge) is also a chromium-based option.
            # We can make the browser choice configurable later.
            self.browser = await self.playwright.chromium.launch(headless=True) # Launch headless for testing in this environment
            self.page = await self.browser.new_page()
            self._is_initialized = True
            print("BrowserManager initialized: Playwright started, browser launched, page created.")

    async def open_url(self, url: str):
        """Navigates to the specified URL."""
        await self._ensure_initialized()
        if not self.page:
            print("Error: Page not available.")
            return

        print(f"Navigating to URL: {url}")
        try:
            # Ensure URL has a scheme
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            await self.page.goto(url, timeout=60000) # 60 seconds timeout
            print(f"Successfully navigated to: {url}")
            # Bring page to front in case it was obscured
            await self.page.bring_to_front()
        except Exception as e:
            print(f"Error navigating to {url}: {e}")

    async def search_web(self, query: str, search_engine_url: str = "https://www.google.com"):
        """Performs a web search on the specified search engine."""
        await self._ensure_initialized()
        if not self.page:
            print("Error: Page not available.")
            return

        # A more robust way for Google search (handles queries with spaces etc.)
        search_query_url = f"{search_engine_url}/search?q={query}"
        print(f"Searching for: '{query}' using URL: {search_query_url}")
        try:
            await self.page.goto(search_query_url, timeout=60000)
            print(f"Search page loaded for query: '{query}'")
            await self.page.bring_to_front()
        except Exception as e:
            print(f"Error during web search for '{query}': {e}")

    async def close(self):
        """Closes the browser and stops Playwright."""
        if self.browser:
            await self.browser.close()
            print("Browser closed.")
        if self.playwright:
            await self.playwright.stop()
            print("Playwright stopped.")
        self._is_initialized = False

# Example Usage (for testing this module directly)
async def main_test():
    manager = BrowserManager()

    # Test opening a URL
    await manager.open_url("example.com")
    await asyncio.sleep(2) # Keep browser open for a bit

    # Test searching
    await manager.search_web("Playwright Python")
    await asyncio.sleep(2)

    # Test opening another URL in the same browser/page
    await manager.open_url("https://playwright.dev/python")
    await asyncio.sleep(5) # Keep browser open

    await manager.close()

if __name__ == "__main__":
    # This allows running this file directly to test its functionality.
    # In a real application, other modules would import and use BrowserManager.
    asyncio.run(main_test())
