import asyncio
import sys
import os
import time

# Add the project root to the path so we can import from ergon
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ergon.core.agents.browser.service import BrowserService

async def test_browser():
    """Test the browser service with a simple Google search for Chinese lunar calendar 1935"""
    print("Initializing browser service...")
    browser_service = BrowserService(headless=False)
    
    try:
        print("Navigating to Google...")
        result = await browser_service.navigate("https://www.google.com")
        print(result)
        await asyncio.sleep(2)
        
        print("Typing search query...")
        result = await browser_service.type('textarea[name="q"]', "Chinese lunar calendar 1935")
        print(result)
        
        print("Clicking search button...")
        result = await browser_service.click('input[name="btnK"]')
        print(result)
        await asyncio.sleep(3)
        
        print("Getting page text...")
        text = await browser_service.get_text()
        print(f"Found text (first 500 chars): {text[:500]}")
        
        print("Taking screenshot...")
        result = await browser_service.screenshot()
        print(result)
        
        print("Scrolling down...")
        result = await browser_service.scroll("down", amount=500)
        print(result)
        await asyncio.sleep(1)
        
        print("Test completed successfully!")
    except Exception as e:
        print(f"Error during test: {str(e)}")
    finally:
        print("Closing browser...")
        await browser_service.close()

if __name__ == "__main__":
    asyncio.run(test_browser())