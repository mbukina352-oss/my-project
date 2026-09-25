"""Квартиры и планировки из TrendAgent через тот же API, которым пользуется сайт.

Вход делается один раз вручную (login.command): бот хранит cookie браузера и
берёт из них ключ доступа (auth_token), который сайт подставляет в запросы к
api.trendagent.ru.
"""
import asyncio
import base64
import logging
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.async_api import Browser, BrowserContext, async_playwright

from .config import TrendAgent
from .models import Flat
from .names import find_blocks

log = logging.getLogger(__name__)

API = "https://api.trendagent.ru/v4_29"
IMAGES = "https://selcdn.trendagent.ru/images/"
BLOCKS_TTL = 6 * 3600

FINISHING = {
    0: "Без отделки", 1: "Чистовая", 2: "Подчистовая", 4: "С мебелью",
    10: "С ремонтом", 20: "Без стен", 30: "С техникой",
}


class LoginRequired(Exception):
    """Нет сохранённого входа или он истёк: нужно запустить login.command."""


class NotFound(Exception):
    """ЖК не найден или название неоднозначное."""

    def __init__(self, suggestions: list[str]):
        super().__init__(", ".join(suggestions))
        self.suggestions = suggestions


def rooms_from_code(code: int) -> tuple[int | None, bool]:
    """Код комнат TrendAgent → (комнат, евро). 0 — студия, 22 — евро-2 и т. д."""
    if code in (0, 1, 2, 3, 4, 5, 6, 7):
        return code, False
    if 21 <= code <= 29:
        return code - 20, True
    return None, False


def plan_url(plan: dict | None) -> str:
    if not plan or not plan.get("file_name"):
        return ""
    return IMAGES + (plan.get("path") or "") + plan["file_name"]


def parse_block_apartments(payload: dict, block_name: str = "", address: str = "") -> list[Flat]:
    """Ответ /apartments/block/<id>/search/ → список свободных квартир."""
    flats = []
    groups = ((payload.get("data") or {}).get("results") or {}).values()
    for group in groups:
        for g in group:
            for a in g.get("apartments") or []:
                status = (a.get("status") or {}).get("name", "")
                if status and not status.lower().startswith("свобод"):
                    continue
                rooms, euro = rooms_from_code(int(a.get("rooms", -1)))
                flats.append(Flat(
                    complex_name=block_name,
                    address=address,
                    building=" ".join(str(a.get("building_name", "")).split()),
                    rooms=rooms,
                    euro=euro,
                    area=float(a["privArea"]) if a.get("privArea") else None,
                    floor=str(a.get("floor", "")),
                    price=int(a["price"]) if a.get("price") else None,
                    deadline=a.get("deadline", ""),
                    finishing=FINISHING.get(a.get("finishing_id"), ""),
                    plan_url=plan_url(a.get("plan")),
                ))
    return flats


class TrendAgentClient:
    def __init__(self, cfg: TrendAgent):
        self.cfg = cfg
        self._pw = None
        self._browser: Browser | None = None
        self._ctx: BrowserContext | None = None
        self._state_mtime = 0.0
        self._token = ""
        self._blocks: list[dict] = []
        self._blocks_at = 0.0
        self._lock = asyncio.Lock()

    async def _context(self) -> BrowserContext:
        state = Path(self.cfg.state_file)
        if not state.is_file():
            raise LoginRequired()
        mtime = state.stat().st_mtime
        if self._ctx and mtime == self._state_mtime:
            return self._ctx
        # Вход обновили через login.command: пересоздаём браузер с новыми cookie
        await self.close()
        self._state_mtime = mtime
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=True)
        self._ctx = await self._browser.new_context(
            storage_state=str(state), locale="ru-RU", viewport={"width": 1440, "height": 900},
        )
        return self._ctx

    async def _fetch_token(self) -> str:
        """Открывает сайт и перехватывает auth_token из его запросов к API."""
        ctx = await self._context()
        page = await ctx.new_page()
        found: asyncio.Future[str] = asyncio.get_running_loop().create_future()

        def on_request(req):
            if "api.trendagent.ru" in req.url and not found.done():
                token = parse_qs(urlparse(req.url).query).get("auth_token", [""])[0]
                if token:
                    found.set_result(token)

        page.on("request", on_request)
        try:
            await page.goto(self.cfg.site_url, wait_until="domcontentloaded")
            try:
                return await asyncio.wait_for(found, 30)
            except asyncio.TimeoutError:
                if "sso." in page.url or "login" in page.url:
                    raise LoginRequired()
                raise RuntimeError(f"Не удалось получить ключ TrendAgent, страница: {page.url}")
        finally:
            await page.close()

    async def _api(self, path: str, **params) -> dict:
        ctx = await self._context()
        for attempt in range(2):
            if not self._token:
                self._token = await self._fetch_token()
            resp = await ctx.request.get(
                API + path,
                params={**params, "auth_token": self._token, "city": self.cfg.city_id, "lang": "ru"},
            )
            if resp.status in (401, 403) and attempt == 0:
                log.info("Ключ TrendAgent устарел, обновляю")
                self._token = ""
                continue
            if resp.status in (401, 403):
                raise LoginRequired()
            if not resp.ok:
                raise RuntimeError(f"TrendAgent {path}: HTTP {resp.status}")
            return await resp.json()
        raise LoginRequired()

    async def _all_blocks(self) -> list[dict]:
        if not self._blocks or time.time() - self._blocks_at > BLOCKS_TTL:
            data = await self._api("/blocks/search/", show_type="map")
            self._blocks = (data.get("data") or {}).get("results") or []
            self._blocks_at = time.time()
            log.info("TrendAgent: загружено %s ЖК", len(self._blocks))
        return self._blocks

    async def find_block(self, name: str) -> dict:
        ranked = find_blocks(name, await self._all_blocks())
        if not ranked:
            raise NotFound([])
        best_score, best = ranked[0]
        second = ranked[1][0] if len(ranked) > 1 else 0.0
        if best_score >= 0.8 and (best_score == 1.0 or best_score - second >= 0.05):
            return best
        if best_score >= 0.7 and best_score - second >= 0.1:
            return best
        raise NotFound([b["name"] for s, b in ranked if s >= 0.5])

    async def search(self, complex_name: str) -> tuple[str, list[Flat]]:
        """Возвращает (название ЖК в TrendAgent, свободные квартиры)."""
        async with self._lock:
            block = await self.find_block(complex_name)
            block_id = block["_id"]
            address = ""
            try:
                info = await self._api(f"/blocks/{block_id}/unified/")
                address = (info.get("data") or {}).get("address") or ""
            except Exception:
                log.warning("Не удалось получить адрес ЖК", exc_info=True)
            data = await self._api(f"/apartments/block/{block_id}/search/")
            flats = parse_block_apartments(data, block.get("name", ""), address)
            log.info("TrendAgent: %s — %s свободных квартир", block.get("name"), len(flats))
            return block.get("name", complex_name), flats

    async def download(self, flat: Flat) -> None:
        if flat.plan_image or not flat.plan_url:
            return
        ctx = await self._context()
        resp = await ctx.request.get(flat.plan_url)
        if not resp.ok:
            log.warning("Планировка не скачалась: HTTP %s %s", resp.status, flat.plan_url)
            return
        data = await resp.body()
        if data[:500].lstrip().lower().startswith((b"<svg", b"<?xml")):
            data = await self._svg_to_png(ctx, data)
        flat.plan_image = data

    @staticmethod
    async def _svg_to_png(ctx: BrowserContext, svg: bytes) -> bytes:
        """Планировки бывают в SVG: рисуем их в браузере и снимаем скриншот."""
        page = await ctx.new_page()
        try:
            await page.set_content(
                "<body style='margin:0;background:#fff'>"
                "<img id=p style='width:2000px' src='data:image/svg+xml;base64,"
                + base64.b64encode(svg).decode() + "'></body>"
            )
            return await page.locator("#p").screenshot(type="png")
        finally:
            await page.close()

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()
        self._pw = self._browser = self._ctx = None
        self._token = ""
