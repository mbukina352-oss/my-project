"""Telegram-бот: «Джойс 35млн 60м2» → PDF с планировками и вашими контактами."""
import asyncio
import io
import logging

import pypdfium2 as pdfium
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import BufferedInputFile, Message

from .config import settings
from .matching import closest_flats, pick_flats
from .models import Flat
from .pdf import build_pdf
from .query import Query, parse_query
from .trendagent import LoginRequired, NotFound, TrendAgentClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bot")

dp = Dispatcher()
ta = TrendAgentClient(settings.trendagent)

HELP = (
    "Пришлите запрос, например:\n"
    "<code>Джойс 35млн 60м2</code>\n"
    "<code>Level Мичуринский 2к 25 млн</code>\n"
    "<code>Шагал студия 30м2</code>\n\n"
    "Я найду подходящие квартиры в TrendAgent и пришлю PDF с планировками и вашими контактами.\n\n"
    "Если нужна конкретная планировка, пришлите её картинкой или PDF, а в подписи напишите "
    "ЖК, цену и площадь. Я оформлю её в ваш PDF."
)


def allowed(message: Message) -> bool:
    return not settings.allowed_users or (message.from_user and message.from_user.id in settings.allowed_users)


def make_pdf(flats: list[Flat]) -> bytes:
    return build_pdf(flats, settings.agent, settings.font_path, settings.font_bold_path)


def file_name(q: Query) -> str:
    name = q.complex_name or "planirovka"
    return "".join(ch if ch.isalnum() or ch in " -_" else "_" for ch in name).strip() + ".pdf"


@dp.message(CommandStart())
@dp.message(Command("help"))
async def start(message: Message) -> None:
    if not allowed(message):
        await message.answer(f"Нет доступа. Ваш Telegram ID: <code>{message.from_user.id}</code>")
        return
    await message.answer(HELP)


@dp.message(Command("id"))
async def my_id(message: Message) -> None:
    await message.answer(f"Ваш Telegram ID: <code>{message.from_user.id}</code>")


@dp.message(F.photo | F.document)
async def from_file(message: Message, bot: Bot) -> None:
    """Режим без поиска: планировка приходит файлом, бот оформляет её в PDF."""
    if not allowed(message):
        return
    q = parse_query(message.caption or "")
    if message.photo:
        file_id = message.photo[-1].file_id
        mime = "image/jpeg"
    else:
        file_id = message.document.file_id
        mime = message.document.mime_type or ""
    buf = io.BytesIO()
    await bot.download(file_id, destination=buf)
    data = buf.getvalue()

    if mime == "application/pdf" or data[:4] == b"%PDF":
        page = pdfium.PdfDocument(data)[0]
        out = io.BytesIO()
        page.render(scale=3).to_pil().save(out, "PNG")
        data = out.getvalue()
    elif not mime.startswith("image/"):
        await message.answer("Пришлите планировку картинкой (JPG/PNG) или PDF.")
        return

    flat = Flat(complex_name=q.complex_name, price=q.price, area=q.area, rooms=q.rooms, plan_image=data)
    pdf = make_pdf([flat])
    await message.answer_document(BufferedInputFile(pdf, file_name(q)), caption=q.describe())


@dp.message(F.text)
async def search(message: Message) -> None:
    if not allowed(message):
        return
    q = parse_query(message.text)
    if not q.complex_name:
        await message.answer("Не понял название ЖК. " + HELP)
        return
    status = await message.answer(f"Ищу: {q.describe()}…")
    try:
        block_name, flats = await ta.search(q.complex_name)
    except LoginRequired:
        await status.edit_text(
            "Бот не вошёл в TrendAgent. На компьютере остановите бота (Control+C) и выполните:\n"
            "<code>bash login.command</code>\n"
            "Войдите в TrendAgent в открывшемся окне, вернитесь в Терминал, нажмите Enter "
            "и снова запустите <code>bash start.command</code>."
        )
        return
    except NotFound as e:
        if e.suggestions:
            await status.edit_text("Не понял, какой ЖК. Может быть: " + ", ".join(e.suggestions) + "?")
        else:
            await status.edit_text(f"Не нашёл ЖК «{q.complex_name}» в TrendAgent (Москва).")
        return
    except Exception:
        log.exception("Ошибка поиска в TrendAgent")
        await status.edit_text("TrendAgent не ответил. Попробуйте ещё раз через минуту.")
        return

    note = ""
    found = pick_flats(flats, q, settings.price_tolerance, settings.area_tolerance, settings.max_results)
    if not found:
        found = closest_flats(flats, q, settings.max_results)
        note = "Точно под запрос нет, вот ближайшие варианты:\n"
    if not found:
        await status.edit_text(f"В ЖК «{block_name}» сейчас нет свободных квартир с планировками.")
        return

    await asyncio.gather(*(ta.download(f) for f in found))
    found = [f for f in found if f.plan_image]
    if not found:
        await status.edit_text("Квартиры нашёл, но не смог скачать планировки.")
        return

    pdf = make_pdf(found)
    lines = [
        f"• {f.rooms_label} {f.area:g} м²".replace(".", ",")
        + f", {f.floor} эт., " + f"{f.price:,} ₽".replace(",", " ")
        for f in found
    ]
    q.complex_name = block_name
    caption = f"ЖК «{block_name}»\n" + note + "\n".join(lines)
    await message.answer_document(BufferedInputFile(pdf, file_name(q)), caption=caption[:1000])
    await status.delete()


async def main() -> None:
    if not settings.bot_token:
        raise SystemExit("Не задан BOT_TOKEN в .env")
    from aiogram.client.default import DefaultBotProperties

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    try:
        await dp.start_polling(bot)
    finally:
        await ta.close()


if __name__ == "__main__":
    asyncio.run(main())
