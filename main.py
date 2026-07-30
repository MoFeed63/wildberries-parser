import sqlite3
import os
from playwright.async_api import async_playwright
import asyncio

BD_PATH = os.path.join(os.path.dirname(__file__), "wb.db")

async def main():
    responses = []

    conn = sqlite3.connect(BD_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wb (
                article INTEGER UNIQUE,
                name TEXT UNIQUE,
                brand TEXT,
                price REAL,
                link TEXT
            )
        """)

        def handle_response(response):
            if "exactmatch" in response.url:
                responses.append(response)

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            page.on("response", handle_response)
            await page.goto("https://www.wildberries.ru/catalog/0/search.aspx?search=люстры")
            await page.wait_for_timeout(5000)

            if responses:
                data = await responses[0].json()
                print(data)
                products = data['products'][:5]
                result = []
                for p in products:
                    sizes = p.get("sizes")
                    first = sizes[0] if sizes else {}
                    price = first.get("price")
                    result.append({
                        "article": p.get("id"),
                        "name": p.get("name"),
                        "barnd": p.get("brand"),
                        "price": price.get("product", 0) / 100,
                        "link": f"https://www.wildberries.ru/catalog/{p.get("id")}/detail.aspx"
                        

                    })
                    cursor.execute("INSERT OR IGNORE INTO wb (article, name, brand, price, link) VALUES (?, ?, ?, ?, ?)", (p.get("id"), p.get("name"), p.get("brand"), price.get("product", 0) / 100, f"https://www.wildberries.ru/catalog/{p.get("id")}/detail.aspx"))
                    
                print(result)
            else:
                print("Нет ответов")
            await browser.close()
            conn.commit()
    finally:
        conn.close()

asyncio.run(main())
        