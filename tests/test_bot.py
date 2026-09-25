import io

import pytest
from PIL import Image, ImageDraw

from bot.config import Agent
from bot.matching import pick_flats
from bot.models import Flat
from bot.pdf import build_pdf
from bot.query import parse_query
from bot.names import find_blocks
from bot.trendagent import parse_block_apartments

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


@pytest.mark.parametrize("text,name,price,area,rooms", [
    ("Джойс 35млн 60м2", "Джойс", 35_000_000, 60, None),
    ("ЖК Джойс 35 млн 60 м2", "Джойс", 35_000_000, 60, None),
    ("Level Мичуринский 2к 25,5 млн", "Level Мичуринский", 25_500_000, None, 2),
    ("Шагал студия 30м²", "Шагал", None, 30, 0),
    ("Джойс 35м 60кв", "Джойс", 35_000_000, 60, None),
    ("Символ 18 500 000 45.5 кв.м", "Символ", 18_500_000, 45.5, None),
    ("пришли хай лайф планировку 30м2 30млн", "хай лайф", 30_000_000, 30, None),
])
def test_parse_query(text, name, price, area, rooms):
    q = parse_query(text)
    assert (q.complex_name, q.price, q.area, q.rooms) == (name, price, area, rooms)


def test_parse_block_apartments():
    # Урезанный ответ /v4_29/apartments/block/<id>/search/
    payload = {"data": {"results": {"2#4 кв. 2027": [{"apartments": [
        {"plan": {"path": "o/h/", "file_name": "plan.png"}, "status": {"name": "Свободная (акция)"},
         "floor": 5, "price": 28417518, "rooms": 0, "privArea": 25.7, "deadline": "4 кв. 2027",
         "building_name": "5  Mind Tower", "finishing_id": 1},
        {"plan": {"path": "a/b/", "file_name": "e2.png"}, "status": {"name": "Свободная"},
         "floor": 18, "price": 52092096, "rooms": 22, "privArea": 50.9, "finishing_id": 2},
        {"plan": {"path": "a/b/", "file_name": "x.png"}, "status": {"name": "Бронь"},
         "floor": 3, "price": 1, "rooms": 1, "privArea": 40},
    ]}]}}}
    flats = parse_block_apartments(payload, "HIGH LIFE", "ул Летниковская")
    assert len(flats) == 2  # бронь пропущена
    studio, euro = flats
    assert studio.plan_url == "https://selcdn.trendagent.ru/images/o/h/plan.png"
    assert (studio.rooms_label, studio.area, studio.building, studio.finishing) == (
        "Студия", 25.7, "5 Mind Tower", "Чистовая")
    assert (euro.rooms, euro.euro, euro.rooms_label) == (2, True, "Евро-2")


BLOCKS = [{"name": "HIGH LIFE", "guid": "high-life"}, {"name": "Джойс", "guid": "jois"},
          {"name": "Инджой", "guid": "injoy"}, {"name": "Dream Towers", "guid": "dream-towers"},
          {"name": "ЗилАрт", "guid": "zilart"}, {"name": "ВОЙС", "guid": "voice"}]


@pytest.mark.parametrize("query,expected", [
    ("хай лайф", "HIGH LIFE"), ("High Life", "HIGH LIFE"), ("джойс", "Джойс"),
    ("дрим тауэрс", "Dream Towers"), ("зил арт", "ЗилАрт"), ("инджой", "Инджой"),
])
def test_find_blocks(query, expected):
    assert find_blocks(query, BLOCKS)[0][1]["name"] == expected


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
