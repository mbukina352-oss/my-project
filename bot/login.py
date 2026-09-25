"""Вход в TrendAgent вручную в открытом окне браузера.

Бот запоминает вход (cookie), поэтому пароль в .env не нужен. Заодно
сохраняет, какие данные сайт загружает на страницах ЖК (data/capture.json),
чтобы по ним можно было настроить поиск квартир.
"""
import asyncio
import json
import subprocess
import sys
from pathlib import Path

from playwright.async_api import async_playwright

from .config import settings

CAPTURE = Path("data/capture.json")
MAX_BODY = 300_000  # символов на один ответ
MAX_TOTAL = 8_000_000


async def main() -> None:
    cfg = settings.trendagent
    state = Path(cfg.state_file)
    state.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    pages: list[str] = []
    total = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        ctx = await browser.new_context(
            storage_state=str(state) if state.is_file() else None,
            locale="ru-RU",
            viewport={"width": 1440, "height": 900},
        )

        async def on_response(resp):
            nonlocal total
            if "trendagent" not in resp.url or "json" not in (resp.headers.get("content-type") or ""):
                return
            try:
                body = await resp.text()
            except Exception:
                return
            if total > MAX_TOTAL:
                return
            total += min(len(body), MAX_BODY)
            records.append({"url": resp.url, "status": resp.status, "body": body[:MAX_BODY]})

        ctx.on("response", on_response)
        ctx.on("page", lambda p: p.on("framenavigated", lambda f: f == p.main_frame and pages.append(f.url)))

        page = await ctx.new_page()
        page.on("framenavigated", lambda f: f == page.main_frame and pages.append(f.url))
        await page.goto("https://msk.trendagent.ru/")

        print()
        print("Открылось окно браузера. В нём:")
        print("  1. Войдите в TrendAgent (если попросит).")
        print("  2. Найдите любой ЖК, например «Хай Лайф», и откройте его страницу.")
        print("  3. Откройте список квартир этого ЖК и полистайте его вниз.")
        print("  4. Откройте одну квартиру, чтобы была видна планировка.")
        print()
        await asyncio.to_thread(input, "Когда закончите, вернитесь сюда и нажмите Enter... ")

        await ctx.storage_state(path=str(state))
        await browser.close()

    CAPTURE.write_text(
        json.dumps({"pages": pages, "responses": records}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print()
    print("Готово! Вход сохранён, бот будет заходить в TrendAgent сам.")
    print(f"Сохранено ответов сайта: {len(records)}.")
    print(f"Файл для настройки поиска: {CAPTURE.resolve()}")
    if sys.platform == "darwin":
        subprocess.run(["open", "-R", str(CAPTURE)])


if __name__ == "__main__":
    asyncio.run(main())
