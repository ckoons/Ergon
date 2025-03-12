import asyncio
from browser_use import Agent, Browser, BrowserConfig, BrowserContextConfig

async def main():
    print("Initializing browser...")
    browser_config = BrowserConfig(headless=False)
    browser = Browser()
    
    context_config = BrowserContextConfig()
    context = await browser.new_context(config=context_config)
    
    print("Getting page...")
    page = context.page
    
    print("Navigating to Google...")
    await page.goto("https://www.google.com")
    await asyncio.sleep(2)
    
    print("Searching...")
    try:
        await page.fill('textarea[name="q"]', "Chinese lunar calendar 1935")
        await page.press('textarea[name="q"]', "Enter")
        await asyncio.sleep(3)
    
        print("Getting content...")
        content = await page.content()
        text = await page.evaluate("() => document.body.innerText")
        print(f"Page text (first 500 chars): {text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("Closing browser...")
    await browser.close()
    print("Done")

if __name__ == "__main__":
    asyncio.run(main())