import sqlite3
import os
import asyncio
import json
from camoufox.async_api import AsyncCamoufox


BD_PATH = os.path.join(os.path.dirname(__file__), "wb.db")


async def main():
    conn = sqlite3.connect(BD_PATH)
    responses = []

    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("SELECT article, price FROM wb ORDER BY rowid ASC")
        rows = cursor.fetchall()
        if not rows:
            print("Таблица wb пуста. Нечего обрабатывать.")
            return
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS details (
                article INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                brand TEXT,
                description TEXT,
                options TEXT,
                subj_name TEXT,
                contents TEXT,
                price REAL,
                FOREIGN KEY (article) REFERENCES wb (article) ON DELETE CASCADE
            )
        """)
        
        current_data = None

        async def handle_response_card(response):
            nonlocal current_data
            if "card.json" in response.url:
                try:
                    current_data = await response.json()
                except Exception:
                    pass

        async with AsyncCamoufox(headless=True) as browser:
            page = await browser.new_page()
            page.on("response", handle_response_card)
            result = []
            for article, price in rows:
                current_data = None
                
                await page.goto(f"https://www.wildberries.ru/catalog/{article}/detail.aspx")
                await page.wait_for_timeout(5000)
            
                if current_data:
                    try:
                        p = current_data
                        
                        name = p.get('imt_name', '')
                        brand = p.get('selling', {}).get('brand_name', '')
                        description = p.get('description', '')
                        options = json.dumps(p.get("options", []), ensure_ascii=False)
                        subj_name = p.get("subj_name", '')
                        contents = p.get("contents", '')
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
                        cursor.execute("INSERT OR IGNORE INTO details (article, name, brand, description, options, subj_name, contents, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                                        (article, name, brand, description, options, subj_name, contents, price))
                    except KeyError as e:
                            print(f"Ошибка парсинга JSON для артикула {article}: отсутствует ключ {e}")
                else:
                    print(f"Не удалось перехватить card.json для артикула {article}")

        conn.commit()
    finally:
        conn.close()


asyncio.run(main())
