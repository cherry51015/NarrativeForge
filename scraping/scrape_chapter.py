import asyncio
from playwright.async_api import async_playwright

url = "https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1"
ss_path = "ss.png" 
txt_path = "content.txt"

async def scrape_chapter(url, screenshot_file,text_file):
   async with async_playwright() as p:
       browser = await p.chromium.launch(headless=True)
       page = await browser.new_page()
       await page.goto(url)
       await page.screenshot(path=screenshot_file, full_page=True)  
    
       content_div = await page.query_selector("#mw-content-text")
       if content_div:
           text = await content_div.inner_text()
       else:
           text = "couldn't find the main content"
       with open(text_file,"w",encoding="utf-8") as f:
           f.write(text)
       await browser.close()
if __name__ == "__main__":
    asyncio.run(scrape_chapter(url, ss_path, txt_path))
    print(f"scraped chapter - saved screenshot and text")