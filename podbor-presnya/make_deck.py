"""Презентации подбора: квартира 180–200 м², терраса 50–80 м², Пресненский р-н внутри ТТК,
готовое или сдача не позже I кв. 2027, бюджет до 259 млн ₽.

Собирает HTML-слайды 1920×1080 в стиле AXLEV ESTATE; render.js печатает их в PDF:
общая презентация подбора и отдельная презентация по каждому объекту.

Данные из открытых источников на 02.10.2026 (TrendAgent из облака недоступен).
"""
import html
import json
from pathlib import Path

HERE = Path(__file__).parent
COVER = (HERE.parent / "axlev" / "axlev-estate.png").resolve().as_uri()
DATE = "02.10.2026"

BRIEF = [
    ("Площадь", "180–200 м²"),
    ("Терраса", "50–80 м²"),
    ("Срок", "готовое или до I кв. 2027"),
    ("Локация", "Пресненский р-н, внутри ТТК"),
    ("Бюджет", "до 259 млн ₽"),
]

OBJECTS = [
    {
        "slug": "01-fantastic-house",
        "verdict": "Точное попадание",
        "verdict_kind": "ok",
        "name": "Fantastic House",
        "subtitle": "Клубный дом deluxe на Тишинке · исторический фасад 1908 года",
        "address": "ул. Малая Грузинская, 44/30, стр. 1 (угол Б. Тишинского пер.), Пресненский р-н, ЦАО",
        "lot_title": "Пентхаус с террасой и камином",
        "price": "190 000 000 ₽",
        "price_note": "≈ 1,03 млн ₽/м² · запас к бюджету ≈ 69 млн ₽",
        "params": [
            ("Площадь", "184,5 м²"),
            ("Терраса", "57,3 м²"),
            ("Комнат", "4"),
            ("Этаж", "5 (верхний)"),
            ("Потолки", "4,3 м"),
            ("Статус", "Дом сдан (2022)"),
        ],
        "checks": [
            ("Площадь 180–200 м²", "184,5 м²", "ok"),
            ("Терраса 50–80 м²", "57,3 м²", "ok"),
            ("Готовое / до I кв. 2027", "Дом сдан", "ok"),
            ("Пресненский р-н, внутри ТТК", "Тишинка, между Садовым и ТТК", "ok"),
            ("Бюджет до 259 млн ₽", "190 млн ₽", "ok"),
        ],
        "about": [
            "Камерный клубный дом: всего 24 квартиры, 3 пентхауса на 5-м этаже — с каминами и террасами.",
            "В пентхаусе дровяной камин в гостиной, окна на три стороны света.",
            "Застройщик — СЗ «Полинессо». Высота потолков в доме 3,3–3,5 м, в пентхаусах до 4,3 м.",
            "Около 18 минут пешком до Патриарших прудов; рядом Тишинская площадь, Белорусская.",
        ],
        "also": "В этом же доме ещё один пентхаус — 232,6 м² за 279,1 млн ₽: больше и дороже заданных рамок.",
        "todo": "Объявление из открытых источников: до показа подтвердить, что лот свободен и цена актуальна.",
        "sources": [
            ("Славянский Двор, лот 51669", "https://www.slrealty.ru/elite/sale/51669"),
            ("Metrium, ID 23797", "https://www.metrium.ru/elitnaya-gorodskaya-nedvijimost/elitnie-kvartiri/23797/"),
        ],
    },
    {
        "slug": "03-dom-na-tishinke",
        "verdict": "Скорее вне бюджета",
        "verdict_kind": "no",
        "name": "Дом на Тишинке",
        "subtitle": "DELUXE от «Донстрой» · дом сдан в 2021 году",
        "address": "Средний Тишинский пер., 5–7, Пресненский р-н, ЦАО",
        "lot_title": "Пентхаус с тёплой и открытой террасой, с дизайнерским ремонтом",
        "price": "≈ 390–450 млн ₽ *",
        "price_note": "* два объявления: ≈ 1,6 млн ₽/м² (≈ 390 млн) и 450 млн ₽; в одном источнике встречалась цифра 221 млн — скорее ошибка",
        "params": [
            ("Тёплый контур", "201,5 м²"),
            ("Терраса", "83 м²"),
            ("Комнат", "4"),
            ("Этаж", "7"),
            ("Потолки", "3,2 м"),
            ("Статус", "Дом сдан, с ремонтом"),
        ],
        "checks": [
            ("Площадь 180–200 м²", "201,5 м² (+1,5)", "warn"),
            ("Терраса 50–80 м²", "83 м² (+3)", "warn"),
            ("Готовое / до I кв. 2027", "Дом сдан", "ok"),
            ("Пресненский р-н, внутри ТТК", "Тишинка, между Садовым и ТТК", "ok"),
            ("Бюджет до 259 млн ₽", "≈ 390–450 млн ₽", "no"),
        ],
        "about": [
            "Кухня изолирована, гостиная-столовая с выходом на террасу, мастер-спальня с гардеробной и ванной.",
            "Ещё спальня, кабинет, гостевой санузел и постирочная.",
            "Отделка: натуральный шпон, мрамор, оникс. Терраса с закрытой тёплой и открытой зонами.",
            "Пентхаусы дома — с патио, каминами и ванными с окнами. Всего в доме 145 квартир.",
        ],
        "also": "Есть и 4-комнатная 164 м² за 185 млн ₽, но без данных о террасе.",
        "todo": "Цена почти вдвое выше бюджета. Имеет смысл только как торг с собственником: площадь и терраса почти в рамках.",
        "sources": [
            ("Циан — вторичка в ЖК «Дом на Тишинке»", "https://www.cian.ru/kupit-kvartiru-vtorichka-zhiloy-kompleks-dom-na-tishinke-48505/"),
            ("Донстрой — о проекте", "https://donstroy.moscow/objects/dom-na-tishinke/"),
        ],
    },
    {
        "slug": "02-myur-meriliz",
        "verdict": "Кандидат на закрытые продажи",
        "verdict_kind": "warn",
        "name": "Мюр & Мерилиз",
        "subtitle": "Клубный дом deluxe на Пресне · 6 пентхаусов на 14–15 этажах",
        "address": "Столярный пер., 3, корп. 6 (угол Малой Грузинской), Пресненский р-н, ЦАО",
        "lot_title": "Пентхаусы с террасами, потолки от 4,7 м",
        "price": "≈ 170–250 млн ₽",
        "price_note": "оценка для 180–200 м² по цене от ≈ 892 тыс. ₽/м²; конкретного лота в открытых источниках нет",
        "params": [
            ("Пентхаусов", "6"),
            ("Этажи", "14–15"),
            ("Потолки", "от 4,7 м"),
            ("Площади в доме", "49–319 м²"),
            ("Квартир всего", "98"),
            ("Срок", "IV кв. 2026"),
        ],
        "checks": [
            ("Площадь 180–200 м²", "пентхаусы до 319 м² — нужна шахматка", "warn"),
            ("Терраса 50–80 м²", "у пентхаусов есть террасы, площадь уточнить", "warn"),
            ("Готовое / до I кв. 2027", "IV кв. 2026 — укладывается", "ok"),
            ("Пресненский р-н, внутри ТТК", "Пресня, у Краснопресненской", "ok"),
            ("Бюджет до 259 млн ₽", "по оценке укладывается", "ok"),
        ],
        "about": [
            "15-этажный дом на месте бывшей мебельной фабрики, фасад с полукруглыми колоннами на всю высоту.",
            "Клубная инфраструктура: кинотеатр, спортзал, детский клуб, коворкинг, сад с амфитеатром.",
            "Проект начинала KR Properties; в декабре 2025 его купила October Group, ввод перенесён на IV кв. 2026.",
            "Новый девелопер перезапускает продажи — пентхаусы часто сначала предлагают агентам закрыто, до сайта.",
        ],
        "also": "",
        "todo": "Запросить у October Group шахматку 6 пентхаусов (площадь, терраса, цена), в том числе лоты закрытых продаж.",
        "sources": [
            ("РБК Недвижимость — о проекте", "https://realty.rbc.ru/news/63fca9039a79477c1cc84328"),
            ("Коммерсантъ — сделка с October Group", "https://www.kommersant.ru/doc/8335380"),
            ("Urbanus — October Group купила проект", "https://www.urbanus.ru/news/2025-12-30/october-group-priobrela-proekt-klubnogo-doma-myur-i-meriliz"),
            ("Metrium — ЖК «Мюр & Мерилиз»", "https://www.metrium.ru/elitnaya-gorodskaya-nedvijimost/zhilie-kompleksi/myur-&-meriliz/"),
        ],
    },
]

OBJECTS.sort(key=lambda o: o["slug"])

# Где искать закрытые (off-market) продажи: в открытых источниках таких лотов нет по определению
CLOSED = [
    ("Мюр & Мерилиз", "October Group",
     "Новый девелопер перезапускает продажи, ввод в IV кв. 2026. Запросить шахматку 6 пентхаусов на 14–15 этажах."),
    ("Fantastic House", "собственники через агентов",
     "Всего 3 пентхауса. Пентхаус 232,6 м² выставлен за 279 млн ₽, можно торговаться. Узнать, не продаётся ли третий."),
    ("Дом на Тишинке", "собственники",
     "Пентхаус 201,5 м² + терраса 83 м² выставлен за 390–450 млн ₽. Цену можно предложить, но разрыв большой."),
    ("SINATRA, Б. Тишинский 38", "вторичка",
     "Пентхаусы до 223 м² с каминами, потолки 5,5 м. Но статус апартаментов, а террасы общие для жильцов."),
]

REJECTED = [
    ("Life Time (Sminex)", "сдан в 2026, внутри ТТК",
     "209 м² — 361 млн ₽; пентхаусы от 424 млн ₽, скай-виллы от 310 млн ₽"),
    ("Тишинский бульвар (Sminex)", "ключи 31.03.2028 и позже",
     "срок позже I кв. 2027; пентхаус 190 м² — 421 млн ₽"),
    ("Lucky (Vesper)", "сдан", "4-комнатные 247–363 м² от 420 млн ₽"),
    ("Republic (Страна / FORMA)", "2026–2027", "лоты до ≈ 140 м², террасы до 16 м²"),
    ("Счастье на Пресне, City Park", "сданы", "Красногвардейский бульвар — за ТТК"),
    ("Бакст (Патриаршие)", "сдан", "≈ 2,5 млн ₽/м²: 2-уровневая 217 м² с террасой — 780 млн ₽"),
    ("Малая Бронная 15", "сдан", "от 520 млн ₽, ≈ 2,7 млн ₽/м²"),
    ("Левенсон (Vesper)", "ключи до 31.08.2027", "срок позже I кв. 2027; от 2,7 млн ₽/м², пентхаусы от 289 м²"),
    ("Дом Спорта (Capital Group)", "сдача I кв. 2029", "срок; 1-комнатные уже от 110 млн ₽"),
]

CSS = """
@page { size: 1920px 1080px; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
:root { --green:#0e2c20; --green2:#173d2d; --gold:#d6b166; --gold-l:#f0dca4; --paper:#f7f3ea;
        --ink:#1d2420; --muted:#6f6a5e; --line:#e2d9c4; --ok:#2f7d4f; --warn:#b07a12; --no:#a3402e; }
.badge.no { background:var(--no); } .st.no { color:var(--no); }
table.tight td, table.tight th { padding:11px 14px; font-size:22px; }
body { font-family: 'Inter', sans-serif; color: var(--ink); }
.slide { width:1920px; height:1080px; position:relative; overflow:hidden; page-break-after:always;
         background: var(--paper); padding: 96px 120px; }
.slide:last-child { page-break-after:auto; }
.serif { font-family:'Cormorant Garamond', serif; }
.cover { background: var(--green) center -170px/1920px 1080px no-repeat; padding:0; }
.cover .shade { position:absolute; inset:0; background:linear-gradient(0deg, rgba(6,23,16,.97) 0%, rgba(6,23,16,.9) 30%, rgba(6,23,16,0) 60%); }
.cover .txt { position:absolute; left:120px; right:120px; bottom:80px; color:var(--gold-l); }
.cover h1 { font-family:'Cormorant Garamond',serif; font-weight:600; font-size:84px; line-height:1.05; color:#fff; }
.cover .sub { margin-top:22px; font-size:30px; color:var(--gold-l); }
.cover .chips { margin-top:36px; display:flex; gap:14px; flex-wrap:wrap; }
.chip { border:1.5px solid var(--gold); color:var(--gold-l); border-radius:40px; padding:10px 22px; font-size:22px; }
.kicker { text-transform:uppercase; letter-spacing:4px; font-size:20px; color:var(--warn); font-weight:600; }
h2 { font-family:'Cormorant Garamond',serif; font-size:76px; font-weight:600; color:var(--green); line-height:1.05; margin-top:10px; }
.lead { font-size:26px; color:var(--muted); margin-top:14px; }
.brand { position:absolute; right:120px; top:56px; font-family:'Cormorant Garamond',serif; letter-spacing:8px;
         color:var(--gold); font-size:26px; font-weight:600; }
.foot { position:absolute; left:120px; right:120px; bottom:44px; font-size:17px; color:var(--muted);
        display:flex; justify-content:space-between; border-top:1px solid var(--line); padding-top:14px; }
.badge { display:inline-block; padding:8px 20px; border-radius:30px; font-size:20px; font-weight:600; color:#fff; }
.badge.ok { background:var(--ok); } .badge.warn { background:var(--warn); }
.grid2 { display:grid; grid-template-columns: 1.15fr 1fr; gap:64px; margin-top:44px; }
.params { display:grid; grid-template-columns:repeat(3,1fr); gap:0; border-top:2px solid var(--green); }
.param { padding:22px 0 20px; border-bottom:1px solid var(--line); }
.param .k { font-size:17px; text-transform:uppercase; letter-spacing:2px; color:var(--muted); }
.param .v { font-size:34px; font-weight:600; color:var(--green); margin-top:6px; }
.price { background:var(--green); color:#fff; padding:36px 40px; border-radius:6px; }
.price .k { font-size:18px; text-transform:uppercase; letter-spacing:3px; color:var(--gold); }
.price .v { font-family:'Cormorant Garamond',serif; font-size:78px; font-weight:600; color:var(--gold-l); line-height:1.1; margin-top:6px; }
.price .n { font-size:20px; color:#cfd8d2; margin-top:8px; line-height:1.4; }
.addr { font-size:24px; margin-top:26px; color:var(--ink); line-height:1.4; }
table { width:100%; border-collapse:collapse; font-size:24px; }
td, th { text-align:left; padding:16px 14px; border-bottom:1px solid var(--line); vertical-align:top; }
th { font-size:17px; text-transform:uppercase; letter-spacing:2px; color:var(--muted); font-weight:600; border-bottom:2px solid var(--green); }
.st { width:44px; font-weight:700; font-size:26px; }
.st.ok { color:var(--ok); } .st.warn { color:var(--warn); }
ul.bul { list-style:none; margin-top:8px; }
ul.bul li { font-size:26px; line-height:1.45; padding-left:30px; position:relative; margin-bottom:16px; }
ul.bul li:before { content:''; position:absolute; left:0; top:15px; width:12px; height:12px; background:var(--gold); }
.note { margin-top:28px; padding:22px 28px; border-left:5px solid var(--gold); background:#efe7d4; font-size:23px; line-height:1.45; }
.src { font-size:21px; line-height:1.7; margin-top:18px; }
.src a { color:var(--green2); }
.cards { display:grid; grid-template-columns:repeat(3,1fr); gap:32px; margin-top:48px; }
.card { background:#fff; border:1px solid var(--line); border-top:6px solid var(--gold); padding:32px; min-height:520px; position:relative; }
.card h3 { font-family:'Cormorant Garamond',serif; font-size:48px; color:var(--green); margin-top:18px; }
.card .p { font-size:40px; font-weight:700; color:var(--green); margin-top:20px; }
.card .l { font-size:23px; color:var(--ink); margin-top:14px; line-height:1.45; }
.card .m { font-size:20px; color:var(--muted); margin-top:14px; line-height:1.4; }
"""

FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700'
         '&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">')


def e(s: str) -> str:
    return html.escape(s)


def foot(page: str) -> str:
    return (f'<div class="foot"><span>AXLEV ESTATE · Подбор: Пресня, 180–200 м² с террасой · {DATE}</span>'
            f'<span>{page}</span></div>')


def cover(title: str, sub: str) -> str:
    chips = "".join(f'<span class="chip">{e(k)}: {e(v)}</span>' for k, v in BRIEF)
    return (f'<section class="slide cover" style="background-image:url(\'{COVER}\')"><div class="shade"></div>'
            f'<div class="txt"><h1>{e(title)}</h1><div class="sub">{e(sub)}</div>'
            f'<div class="chips">{chips}</div></div></section>')


def summary() -> str:
    cards = ""
    for i, o in enumerate(OBJECTS, 1):
        area = next(v for k, v in o["params"] if k in ("Площадь", "Тёплый контур", "Площади в доме"))
        terr = next((f"терраса {v}" for k, v in o["params"] if k == "Терраса"), "террасы у пентхаусов")
        status = o["params"][-1][1]
        cards += (f'<div class="card"><span class="badge {o["verdict_kind"]}">{e(o["verdict"])}</span>'
                  f'<h3>{i}. {e(o["name"])}</h3><div class="p">{e(o["price"])}</div>'
                  f'<div class="l">{e(area)} · {e(terr)}<br>{e(status)}</div>'
                  f'<div class="m">{e(o["address"])}</div></div>')
    return (f'<section class="slide"><div class="brand">AXLEV ESTATE</div><div class="kicker">Итог подбора</div>'
            f'<h2>Три объекта на Пресне внутри ТТК</h2>'
            f'<div class="lead">Под все пять критериев подходит Fantastic House. Мюр & Мерилиз — главный '
            f'кандидат на закрытые продажи. Дом на Тишинке после уточнения цены выходит за бюджет.</div>'
            f'<div class="cards">{cards}</div>{foot("Сводка")}</section>')


def object_slides(o: dict, n: int) -> str:
    params = "".join(f'<div class="param"><div class="k">{e(k)}</div><div class="v">{e(v)}</div></div>'
                     for k, v in o["params"])
    s1 = (f'<section class="slide"><div class="brand">AXLEV ESTATE</div>'
          f'<span class="badge {o["verdict_kind"]}">{e(o["verdict"])}</span>'
          f'<h2>{n}. {e(o["name"])}</h2><div class="lead">{e(o["subtitle"])}</div>'
          f'<div class="grid2"><div><div class="kicker" style="color:var(--green)">{e(o["lot_title"])}</div>'
          f'<div class="params" style="margin-top:18px">{params}</div>'
          f'<div class="addr">📍 {e(o["address"])}</div></div>'
          f'<div><div class="price"><div class="k">Цена</div><div class="v">{e(o["price"])}</div>'
          f'<div class="n">{e(o["price_note"])}</div></div>'
          f'<div class="note">{e(o["todo"])}</div></div></div>{foot(o["name"])}</section>')
    rows = "".join(f'<tr><td class="st {k}">{ {"ok": "✓", "warn": "!", "no": "✗"}[k] }</td><td>{e(c)}</td><td><b>{e(v)}</b></td></tr>'
                   for c, v, k in o["checks"])
    bullets = "".join(f"<li>{e(b)}</li>" for b in o["about"])
    also = f'<div class="note">{e(o["also"])}</div>' if o["also"] else ""
    src = "<br>".join(f'<a href="{e(u)}">{e(t)}</a>' for t, u in o["sources"])
    s2 = (f'<section class="slide"><div class="brand">AXLEV ESTATE</div><div class="kicker">{e(o["name"])}</div>'
          f'<h2>Соответствие запросу</h2><div class="grid2"><div>'
          f'<table><tr><th></th><th>Критерий</th><th>Объект</th></tr>{rows}</table></div>'
          f'<div><div class="kicker" style="color:var(--green)">О доме и лоте</div><ul class="bul" style="margin-top:20px">{bullets}</ul>'
          f'{also}<div class="src"><b>Источники:</b><br>{src}</div></div></div>{foot(o["name"])}</section>')
    return s1 + s2


def rejected() -> str:
    rows = "".join(f"<tr><td><b>{e(a)}</b></td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in REJECTED)
    return (f'<section class="slide"><div class="brand">AXLEV ESTATE</div><div class="kicker">Тоже проверили</div>'
            f'<h2>Почему не вошли в подбор</h2>'
            f'<table class="tight" style="margin-top:36px"><tr><th>Проект</th><th>Статус</th><th>Причина</th></tr>{rows}</table>'
            f'{foot("Отсев")}</section>')


def closed() -> str:
    rows = "".join(f"<tr><td><b>{e(a)}</b></td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in CLOSED)
    return (f'<section class="slide"><div class="brand">AXLEV ESTATE</div><div class="kicker">Закрытые продажи</div>'
            f'<h2>Что запросить вне открытого рынка</h2>'
            f'<div class="lead">Закрытые лоты не публикуют, поэтому здесь не готовые предложения, а адреса для запроса.</div>'
            f'<table style="margin-top:36px"><tr><th>Объект</th><th>Кого спрашивать</th><th>Что запросить</th></tr>{rows}</table>'
            f'<div class="note">Данные из поисковой выдачи на {DATE}: TrendAgent и сайты агрегаторов из облачной среды '
            f'недоступны. В TrendAgent закрытые лоты застройщиков иногда видны агентам — проверьте там «Мюр & Мерилиз».</div>'
            f'{foot("Закрытые продажи")}</section>')


def page(body: str, title: str) -> str:
    return (f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>{e(title)}</title>{FONTS}'
            f'<style>{CSS}</style></head><body>{body}</body></html>')


def main() -> None:
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    jobs = []
    body = cover("Квартира с террасой на Пресне",
                 "Подбор: 3 объекта внутри ТТК · готовое или сдача до I кв. 2027")
    body += summary() + "".join(object_slides(o, i) for i, o in enumerate(OBJECTS, 1)) + closed() + rejected()
    (out / "00-podbor.html").write_text(page(body, "Подбор: Пресня с террасой"), encoding="utf-8")
    jobs.append(["00-podbor.html", "00-Подбор-Пресня-терраса.pdf"])
    for i, o in enumerate(OBJECTS, 1):
        body = cover(o["name"], f'{o["lot_title"]} · {o["price"]}') + object_slides(o, i)
        (out / f'{o["slug"]}.html').write_text(page(body, o["name"]), encoding="utf-8")
        jobs.append([f'{o["slug"]}.html', f'{o["slug"]}.pdf'])
    (out / "jobs.json").write_text(json.dumps(jobs, ensure_ascii=False))


if __name__ == "__main__":
    main()
