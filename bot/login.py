"""Вход в TrendAgent вручную в открытом окне браузера.

Бот запоминает вход (cookie), поэтому пароль в .env не нужен. Заодно
сохраняет, какие данные сайт загружает на страницах ЖК (data/capture.json),
чтобы по ним можно было настроить поиск квартир.
"""
import asyncio
import base64
import json
import subprocess
import traceback
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
    requests: list[dict] = []
    clicks: list[dict] = []
    downloads: list[dict] = []
    total = 0
    presentation = "--presentation" in sys.argv
    errors: list[str] = []
    blobs: list[dict] = []

    try:
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
                    body = (await resp.body()).decode("utf-8", "replace")
                except BaseException:  # noqa: BLE001
                    return
                if total > MAX_TOTAL:
                    return
                total += min(len(body), MAX_BODY)
                records.append({"url": resp.url, "status": resp.status, "body": body[:MAX_BODY]})

            def on_request(req):
                url = req.url
                if "trendagent" not in url and "trend.tech" not in url:
                    return
                interesting = req.method != "GET" or any(
                    w in url.lower() for w in ("present", "pdf", "print", "export", "share", "download"))
                if interesting:
                    requests.append({"method": req.method, "url": url, "type": req.resource_type,
                                     "post": (req.post_data or "")[:20_000]})

            async def on_other_response(resp):
                ctype = resp.headers.get("content-type") or ""
                if "pdf" in ctype or "octet-stream" in ctype:
                    requests.append({"method": "RESPONSE", "url": resp.url, "status": resp.status,
                                     "content_type": ctype, "headers": resp.headers})


            async def on_download(download):
                try:
                    name = Path(download.suggested_filename or "download.pdf").name
                    target = Path("data") / name
                    downloads.append({"url": download.url, "file": str(target), "name": name})
                    await download.save_as(str(target))
                    print(f"\n  Скачан файл: {target}")
                except BaseException as e:  # noqa: BLE001 — запись важнее
                    errors.append(f"download: {e!r}")

            def watch(p):
                p.on("framenavigated", lambda f: f == p.main_frame and pages.append(f.url))
                p.on("download", on_download)

            def on_file(source, data):
                try:
                    _save_file(data)
                except BaseException as e:  # noqa: BLE001
                    errors.append(f"file: {e!r}")

            def _save_file(data):
                name = Path(data.get("name") or f"presentation-{len(downloads) + 1}.pdf").name
                target = Path("data") / name
                target.write_bytes(base64.b64decode(data["b64"]))
                downloads.append({"url": "blob", "file": str(target), "name": name, "stack": data.get("stack", "")})
                print(f"\n  Сохранён PDF: {target}")

            await ctx.expose_binding("__taClick", lambda source, data: clicks.append(data))
            await ctx.expose_binding("__taBlob", lambda source, data: blobs.append(data))
            await ctx.expose_binding("__taFile", on_file)
            await ctx.add_init_script("""
                document.addEventListener('click', (e) => {
                  const el = e.target.closest('button, a, [role=button], label, li, span, div');
                  if (!el || !window.__taClick) return;
                  window.__taClick({
                    text: (el.innerText || el.getAttribute('aria-label') || el.title || '').trim().slice(0, 100),
                    tag: el.tagName, cls: String(el.className || '').slice(0, 200),
                    attrs: Array.from(el.attributes).map(a => a.name + '=' + a.value.slice(0, 80)).join(' ').slice(0, 400),
                    href: el.href || '', url: location.href,
                  });
                }, true);

                // PDF, собранный прямо в браузере (blob): сохраняем его копию
                const origCreate = URL.createObjectURL;
                URL.createObjectURL = function (obj) {
                  const url = origCreate.apply(this, arguments);
                  try {
                    if (obj instanceof Blob && (/pdf/i.test(obj.type) || obj.size > 50000)) {
                      const stack = (new Error().stack || '').slice(0, 3000);
                      window.__taBlob && window.__taBlob({url, type: obj.type, size: obj.size, stack, page: location.href});
                      if (/pdf/i.test(obj.type)) {
                        const r = new FileReader();
                        r.onload = () => window.__taFile && window.__taFile({
                          name: '', b64: String(r.result).split(',')[1], stack});
                        r.readAsDataURL(obj);
                      }
                    }
                  } catch (e) {}
                  return url;
                };
            """)
            ctx.on("request", on_request)
            ctx.on("response", on_response)
            ctx.on("response", on_other_response)
            ctx.on("page", watch)
            page = await ctx.new_page()
            try:
                # Сайт тяжёлый и может грузиться долго: не ждём полной загрузки
                await page.goto(cfg.site_url, wait_until="domcontentloaded", timeout=90_000)
            except BaseException as e:  # noqa: BLE001 — окно всё равно открыто, можно работать
                errors.append(f"goto: {e!r}")

            print()
            print("Открылось окно браузера. В нём:")
            print("  1. Войдите в TrendAgent (если попросит).")
            if presentation:
                print("  2. Откройте любую квартиру (например, в HIGH LIFE).")
                print("  3. Сделайте презентацию этой квартиры так, как делаете обычно,")
                print("     и скачайте PDF.")
            else:
                print("  2. Найдите любой ЖК, например «Хай Лайф», и откройте его страницу.")
                print("  3. Откройте список квартир этого ЖК и полистайте его вниз.")
                print("  4. Откройте одну квартиру, чтобы была видна планировка.")
            print()
            await asyncio.to_thread(input, "Когда закончите, вернитесь сюда и нажмите Enter... ")

            try:
                await ctx.storage_state(path=str(state))
            except BaseException as e:  # noqa: BLE001
                errors.append(f"storage_state: {e!r}")
            try:
                await browser.close()
            except BaseException:  # noqa: BLE001
                pass
    except BaseException:  # noqa: BLE001 — сохраняем то, что успели записать
        errors.append(traceback.format_exc())
        print("\nБраузер закрылся с ошибкой, но запись сохранена.")

    CAPTURE.write_text(
        json.dumps({"pages": pages, "clicks": clicks, "requests": requests, "downloads": downloads, "blobs": blobs, "errors": errors,
                    "responses": records}, ensure_ascii=False, indent=1),
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
