"""PDF с планировкой и данными агента: одна квартира на страницу A4."""
import io
from pathlib import Path

from PIL import Image
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .config import Agent
from .models import Flat

ACCENT = HexColor("#1F3A5F")
MUTED = HexColor("#6B7280")
LINE = HexColor("#E5E7EB")
MARGIN = 36

_fonts_ready = False


def _register_fonts(regular: str, bold: str) -> None:
    global _fonts_ready
    if _fonts_ready:
        return
    pdfmetrics.registerFont(TTFont("Main", regular))
    pdfmetrics.registerFont(TTFont("Main-Bold", bold if Path(bold).is_file() else regular))
    _fonts_ready = True


def _money(v: int | None) -> str:
    return f"{v:,}".replace(",", " ") + " ₽" if v else ""


def _fit(text: str, font: str, size: float, width: float) -> str:
    while text and pdfmetrics.stringWidth(text, font, size) > width:
        text = text[:-2] + "…"
    return text


def _load_image(data: bytes) -> Image.Image:
    head = data[:500].lstrip().lower()
    if head.startswith(b"<svg") or head.startswith(b"<?xml"):
        import cairosvg  # планировки на сайтах часто в SVG

        data = cairosvg.svg2png(bytestring=data, output_width=2000)
    return Image.open(io.BytesIO(data))


def _header(c: canvas.Canvas, agent: Agent, w: float, h: float) -> float:
    bar = 64
    c.setFillColor(ACCENT)
    c.rect(0, h - bar, w, bar, stroke=0, fill=1)
    x = MARGIN
    if agent.logo:
        img = ImageReader(str(agent.logo))
        iw, ih = img.getSize()
        lh = 40
        lw = min(iw * lh / ih, 160)
        c.setFillColor(white)
        c.roundRect(x - 4, h - bar + 8, lw + 8, lh + 8, 4, stroke=0, fill=1)
        c.drawImage(img, x, h - bar + 12, lw, lh, mask="auto", preserveAspectRatio=True)
        x += lw + 20
    c.setFillColor(white)
    c.setFont("Main-Bold", 16)
    c.drawString(x, h - 30, _fit(agent.agency or agent.name, "Main-Bold", 16, w - x - MARGIN))
    if agent.agency and agent.name:
        c.setFont("Main", 10)
        c.drawString(x, h - 47, _fit(agent.name, "Main", 10, w - x - MARGIN))
    return h - bar


def _footer(c: canvas.Canvas, agent: Agent, w: float) -> float:
    bar = 70
    c.setFillColor(ACCENT)
    c.rect(0, 0, w, bar, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("Main-Bold", 13)
    c.drawString(MARGIN, bar - 26, agent.name or agent.agency)
    c.setFont("Main", 11)
    contacts = "   ·   ".join(v for v in (agent.phone, agent.email, agent.telegram) if v)
    c.drawString(MARGIN, bar - 46, _fit(contacts, "Main", 11, w - 2 * MARGIN))
    if agent.agency and agent.name:
        c.setFont("Main", 9)
        c.drawRightString(w - MARGIN, bar - 26, agent.agency)
    return bar


def _params(flat: Flat) -> list[tuple[str, str]]:
    rows = [
        ("Тип", flat.rooms_label),
        ("Площадь", f"{flat.area:g} м²".replace(".", ",") if flat.area else ""),
        ("Этаж", flat.floor),
        ("Корпус", flat.building),
        ("Срок сдачи", flat.deadline),
        ("Отделка", flat.finishing),
    ]
    if flat.price and flat.area:
        rows.append(("Цена за м²", _money(round(flat.price / flat.area))))
    return [(k, v) for k, v in rows if v]


def _page(c: canvas.Canvas, flat: Flat, agent: Agent) -> None:
    w, h = A4
    top = _header(c, agent, w, h)
    bottom = _footer(c, agent, w)

    y = top - 34
    c.setFillColor(ACCENT)
    c.setFont("Main-Bold", 20)
    c.drawString(MARGIN, y, _fit(f"ЖК «{flat.complex_name}»" if flat.complex_name else "Планировка",
                                 "Main-Bold", 20, w * 0.6))
    if flat.price:
        c.setFont("Main-Bold", 20)
        c.drawRightString(w - MARGIN, y, _money(flat.price))
    if flat.address:
        y -= 18
        c.setFillColor(MUTED)
        c.setFont("Main", 10)
        c.drawString(MARGIN, y, _fit(flat.address, "Main", 10, w - 2 * MARGIN))

    params = _params(flat)
    if params:
        y -= 16
        c.setStrokeColor(LINE)
        c.line(MARGIN, y, w - MARGIN, y)
        col_w = (w - 2 * MARGIN) / min(len(params), 4)
        for i, (k, v) in enumerate(params):
            row, col = divmod(i, 4)
            cx = MARGIN + col * col_w
            cy = y - 18 - row * 38
            c.setFillColor(MUTED)
            c.setFont("Main", 8.5)
            c.drawString(cx, cy, k.upper())
            c.setFillColor(HexColor("#111827"))
            c.setFont("Main-Bold", 12)
            c.drawString(cx, cy - 16, _fit(v, "Main-Bold", 12, col_w - 8))
        y -= 18 + ((len(params) - 1) // 4 + 1) * 38
        c.line(MARGIN, y + 6, w - MARGIN, y + 6)

    if flat.plan_image:
        img = _load_image(flat.plan_image)
        if img.mode not in ("RGB", "L"):
            bg = Image.new("RGB", img.size, "white")
            bg.paste(img, mask=img.convert("RGBA").split()[-1])
            img = bg
        box_w, box_h = w - 2 * MARGIN, y - bottom - 24
        scale = min(box_w / img.width, box_h / img.height)
        iw, ih = img.width * scale, img.height * scale
        c.drawImage(ImageReader(img), (w - iw) / 2, bottom + 12 + (box_h - ih) / 2, iw, ih)
    c.showPage()


def build_pdf(flats: list[Flat], agent: Agent, font: str, font_bold: str) -> bytes:
    _register_fonts(font, font_bold)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    title = flats[0].complex_name if flats and flats[0].complex_name else "Планировка"
    c.setTitle(title)
    c.setAuthor(agent.name or agent.agency)
    for flat in flats:
        _page(c, flat, agent)
    c.save()
    return buf.getvalue()
