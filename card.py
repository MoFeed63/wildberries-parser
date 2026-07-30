import sqlite3
import os
import asyncio
from playwright.async_api import async_playwright


BD_PATH = os.path.join(os.path.dirname(__file__), "wb.db")


async def main():
    conn = sqlite3.connect(BD_PATH)
    responses = []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT article FROM wb ORDER BY rowid ASC LIMIT 1")
        row = cursor.fetchone()
        article = row[0]
        cursor.execute("SELECT price FROM wb ORDER BY rowid ASC LIMIT 1")
        price = cursor.fetchone()[0]
        
        
        def handle_response_card(response):
            if "card.json" in response.url:
                responses.append(response)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()


            page.on("response", handle_response_card)
            await page.goto(f"https://www.wildberries.ru/catalog/{article}/detail.aspx")
            await page.wait_for_timeout(5000)
            
            if responses:
                data = await responses[0].json()
                result = []
                # print(data)
                
                name = data['imt_name']
                brand = data['selling']['brand_name']
                description = data['description']
                options = data['options']
                subj_name = data["subj_name"]
                contents = data["contents"]
                result.append({
                    "article": article,
                    "name": name,
                    "brand": brand,
                    "description": description,
                    "options": options,
                    "subj_name": subj_name,
                    "contents": contents,
                    "price": price,
                })
                print(result)
        conn.commit()
    finally:
        conn.close()


asyncio.run(main())
