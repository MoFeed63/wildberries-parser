import sqlite3
import os
from camoufox.async_api import AsyncCamoufox
from playwright_stealth import stealth
import asyncio


BD_PATH = os.path.join(os.path.dirname(__file__), "wb.db")

topic = input("Введите тему запроса: ")

async def main():
    responses = []

    conn = sqlite3.connect(BD_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wb (
                article INTEGER UNIQUE PRIMARY KEY,
                name TEXT UNIQUE,
                brand TEXT,
                price REAL,
                link TEXT
            )
        """)

        async def handle_response(response):
            if "exactmatch" in response.url:
                responses.append(response)

        async with AsyncCamoufox(headless=True) as browser:
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="ru-RU",
                timezone_id="Europe/Moscow"
                )
            page = await context.new_page()

            page.on("response", handle_response)
            await page.goto(f"https://www.wildberries.ru/catalog/0/search.aspx?search={topic}")
            await page.wait_for_timeout(6000)

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
                    cursor.execute("INSERT OR IGNORE INTO wb (article, name, brand, price, link) VALUES (?, ?, ?, ?, ?)", 
                                   (p.get("id"), p.get("name"), p.get("brand"), price.get("product", 0) / 100, f"https://www.wildberries.ru/catalog/{p.get("id")}/detail.aspx"))
                    
                print(result)
            else:
                print("Нет ответов")
            await browser.close()
            conn.commit()
    finally:
        conn.close()

asyncio.run(main())
        