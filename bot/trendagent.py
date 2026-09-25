"""Получение квартир и планировок из личного кабинета TrendAgent.

Публичного API у TrendAgent нет, поэтому бот работает как браузер (Playwright):
входит под вашим логином, открывает поиск по ЖК и собирает JSON-ответы,
которые сайт сам загружает. Из них выбираются объекты, похожие на квартиры
(есть цена, площадь и ссылка на планировку). Имена полей перечислены ниже;
если TrendAgent их поменяет, достаточно поправить списки ключей.
"""
import asyncio
import logging
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import quote, urljoin

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .config import TrendAgent
from .models import Flat

log = logging.getLogger(__name__)

PRICE_KEYS = ("price", "price_total", "cost", "price_base", "min_price")
AREA_KEYS = ("area_total", "area", "area_given", "square", "total_area")
ROOMS_KEYS = ("rooms", "room", "room_count", "rooms_count")
FLOOR_KEYS = ("floor", "floor_number")
PLAN_KEYS = ("plan", "plan_url", "plan_image", "layout", "planning", "image_plan", "plans")
COMPLEX_KEYS = ("block_name", "complex_name", "block", "complex", "object_name")
BUILDING_KEYS = ("building_name", "building", "corpus", "house", "korpus")
DEADLINE_KEYS = ("deadline", "building_deadline", "completion", "ready_date")
FINISHING_KEYS = ("finishing", "finishing_name", "renovation", "decoration")
ADDRESS_KEYS = ("address", "block_address")


def _first(obj: dict, keys: tuple[str, ...]) -> Any:
    for k in keys:
        v = obj.get(k)
        if v not in (None, "", [], {}):
            return v
    return None


def _text(v: Any) -> str:
    if isinstance(v, dict):
        v = _first(v, ("name", "title", "value", "label"))
    if isinstance(v, list):
        v = v[0] if v else ""
        return _text(v)
    return "" if v is None else str(v)


def _number(v: Any) -> float | None:
    if isinstance(v, dict):
        v = _first(v, ("value", "total", "min", "amount"))
    try:
        return float(str(v).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def _url(v: Any) -> str:
    if isinstance(v, str) and (v.startswith("http") or v.startswith("/")):
        return v
    if isinstance(v, dict):
        for k in ("url", "src", "path", "original", "big", "full", "image"):
            if u := _url(v.get(k)):
                return u
    if isinstance(v, list):
        for item in v:
            if u := _url(item):
                return u
    return ""


def _walk(obj: Any) -> Iterator[dict]:
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def extract_flats(payload: Any, base_url: str = "") -> list[Flat]:
    """Находит в произвольном JSON объекты, похожие на квартиры."""
    flats = []
    for obj in _walk(payload):
        price = _number(_first(obj, PRICE_KEYS))
        area = _number(_first(obj, AREA_KEYS))
        plan = _url(_first(obj, PLAN_KEYS))
        if not (price and area and plan) or price < 500_000:
            continue
        rooms = _number(_first(obj, ROOMS_KEYS))
        flats.append(Flat(
            complex_name=_text(_first(obj, COMPLEX_KEYS)),
            address=_text(_first(obj, ADDRESS_KEYS)),
            building=_text(_first(obj, BUILDING_KEYS)),
            rooms=int(rooms) if rooms is not None else None,
            area=round(area, 1),
            floor=_text(_first(obj, FLOOR_KEYS)),
            price=int(price),
            deadline=_text(_first(obj, DEADLINE_KEYS)),
            finishing=_text(_first(obj, FINISHING_KEYS)),
            plan_url=urljoin(base_url, plan),
        ))
    return flats


class TrendAgentClient:
    def __init__(self, cfg: TrendAgent):
        self.cfg = cfg
        self._pw = None
        self._browser: Browser | None = None
        self._ctx: BrowserContext | None = None
        self._lock = asyncio.Lock()

    async def _context(self) -> BrowserContext:
        if self._ctx:
            return self._ctx
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=self.cfg.headless)
        state = Path(self.cfg.state_file)
        self._ctx = await self._browser.new_context(
            storage_state=str(state) if state.is_file() else None,
            locale="ru-RU",
            viewport={"width": 1440, "height": 900},
        )
        return self._ctx

    async def _login(self, page: Page) -> None:
        if not (self.cfg.login and self.cfg.password):
            raise RuntimeError("Не заданы TA_LOGIN / TA_PASSWORD")
        log.info("Вход в TrendAgent")
        await page.goto(self.cfg.login_url, wait_until="domcontentloaded")
        await page.locator(self.cfg.phone_selector).first.fill(self.cfg.login)
        await page.locator(self.cfg.password_selector).first.fill(self.cfg.password)
        await page.locator(self.cfg.submit_selector).first.click()
        await page.wait_for_load_state("networkidle")
        state = Path(self.cfg.state_file)
        state.parent.mkdir(parents=True, exist_ok=True)
        await page.context.storage_state(path=str(state))

    @staticmethod
    def _needs_login(page: Page) -> bool:
        return "sso." in page.url or "/login" in page.url or "/auth" in page.url

    async def search(self, complex_name: str) -> list[Flat]:
        async with self._lock:
            ctx = await self._context()
            page = await ctx.new_page()
            payloads: list[Any] = []

            async def on_response(resp):
                if "json" in (resp.headers.get("content-type") or ""):
                    try:
                        payloads.append(await resp.json())
                    except Exception:
                        pass

            page.on("response", on_response)
            try:
                url = self.cfg.search_url.format(query=quote(complex_name))
                await page.goto(url, wait_until="networkidle")
                if self._needs_login(page):
                    await self._login(page)
                    payloads.clear()
                    await page.goto(url, wait_until="networkidle")
                # Прокрутка, чтобы подгрузились все квартиры
                for _ in range(5):
                    await page.mouse.wheel(0, 4000)
                    await page.wait_for_timeout(700)
                await page.wait_for_load_state("networkidle")

                flats: list[Flat] = []
                seen = set()
                for p in payloads:
                    for f in extract_flats(p, page.url):
                        key = (f.plan_url, f.price, f.area, f.floor)
                        if key not in seen:
                            seen.add(key)
                            flats.append(f)
                if complex_name:
                    needle = complex_name.lower()
                    named = [f for f in flats if needle in f.complex_name.lower()]
                    flats = named or flats
                log.info("TrendAgent: %s квартир по запросу %r", len(flats), complex_name)
                return flats
            finally:
                await page.close()

    async def download(self, flat: Flat) -> None:
        if flat.plan_image or not flat.plan_url:
            return
        ctx = await self._context()
        resp = await ctx.request.get(flat.plan_url)
        if resp.ok:
            flat.plan_image = await resp.body()

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()
