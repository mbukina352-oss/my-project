import io

import pytest
from PIL import Image, ImageDraw

from bot.config import Agent
from bot.matching import pick_flats
from bot.models import Flat
from bot.pdf import build_pdf
from bot.query import parse_query
from bot.trendagent import extract_flats

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


@pytest.mark.parametrize("text,name,price,area,rooms", [
    ("Джойс 35млн 60м2", "Джойс", 35_000_000, 60, None),
    ("ЖК Джойс 35 млн 60 м2", "Джойс", 35_000_000, 60, None),
    ("Level Мичуринский 2к 25,5 млн", "Level Мичуринский", 25_500_000, None, 2),
    ("Шагал студия 30м²", "Шагал", None, 30, 0),
    ("Джойс 35м 60кв", "Джойс", 35_000_000, 60, None),
    ("Символ 18 500 000 45.5 кв.м", "Символ", 18_500_000, 45.5, None),
])
def test_parse_query(text, name, price, area, rooms):
    q = parse_query(text)
    assert (q.complex_name, q.price, q.area, q.rooms) == (name, price, area, rooms)


def test_extract_flats_from_json():
    payload = {"data": {"apartments": [
        {"block_name": "Джойс", "price": 34_900_000, "area_total": 59.8, "room": 2, "floor": 12,
         "plan": {"url": "/media/plan1.png"}, "building": {"name": "Корпус 1"}},
        {"name": "not a flat", "price": 100},
    ]}}
    flats = extract_flats(payload, "https://msk.trendagent.ru/objects/")
    assert len(flats) == 1
    f = flats[0]
    assert f.plan_url == "https://msk.trendagent.ru/media/plan1.png"
    assert (f.complex_name, f.rooms, f.area, f.building) == ("Джойс", 2, 59.8, "Корпус 1")


def test_pick_flats_closest_first():
    q = parse_query("Джойс 35млн 60м2")
    flats = [
        Flat(price=36_000_000, area=61, plan_url="a"),
        Flat(price=35_000_000, area=60, plan_url="b"),
        Flat(price=45_000_000, area=60, plan_url="c"),  # дороже допуска
        Flat(price=30_000_000, area=40, plan_url="d"),  # площадь не подходит
    ]
    assert [f.plan_url for f in pick_flats(flats, q, 0.1, 0.1, 3)] == ["b", "a"]


def _plan_png() -> bytes:
    img = Image.new("RGB", (800, 600), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([50, 50, 750, 550], outline="black", width=8)
    d.line([400, 50, 400, 550], fill="black", width=6)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def test_build_pdf(tmp_path):
    logo = tmp_path / "logo.png"
    Image.new("RGBA", (300, 100), (200, 30, 30, 255)).save(logo)
    agent = Agent(name="Иван Иванов", phone="+7 999 000-00-00", email="ivan@example.ru",
                  agency="Агентство Недвижимости", telegram="@ivan", logo_path=str(logo))
    flats = [Flat(complex_name="Джойс", rooms=2, area=59.8, floor="12", price=34_900_000,
                  building="Корпус 1", deadline="IV кв. 2027", plan_image=_plan_png())] * 2
    pdf = build_pdf(flats, agent, FONT, FONT_BOLD)
    assert pdf.startswith(b"%PDF")
    assert pdf.count(b"/Type /Page\n") + pdf.count(b"/Type /Page ") >= 1
