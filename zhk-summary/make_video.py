"""Рендерит слайды-шпаргалку по 4 ЖК и собирает из них MP4 (1920x1080).

Зависимости: pip install pillow imageio-ffmpeg
Запуск:      python3 zhk-summary/make_video.py
"""
import os
import subprocess
import tempfile

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 30
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ZHK_summary.mp4")

BG = (14, 18, 30)
CARD = (26, 32, 50)
TEXT = (238, 241, 248)
MUTED = (150, 160, 185)
GOOD = (72, 199, 116)
BAD = (240, 90, 90)

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def f(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


ZHK = [
    dict(
        name="АУРА", dev="Мангазея", color=(150, 110, 255),
        tagline="Небоскрёбы в 300 м от метро «Тульская»",
        specs=[
            ("Класс", "Премиум"),
            ("Корпуса", "2 башни, 41–42 эт. + БЦ"),
            ("Квартир", "~916 (28–146 м²)"),
            ("Машиномест", "566"),
            ("Коэф. парковки", "0,62"),
            ("Потолки", "3,2–3,5 м"),
            ("Отделка", "Предчистовая"),
            ("Цена от", "~20–24 млн ₽"),
            ("Срок сдачи", "IV кв. 2027"),
        ],
        pros=["300 м до метро «Тульская» + МЦК рядом",
              "3 мин до ТТК, 8 мин до Садового; паркинг 0,62",
              "Видовые этажи, потолки до 3,5 м, свой БЦ с фитнесом"],
        cons=["Шум и пыль: Тульская эстакада, магистрали",
              "Дорогой м²: на верху до ~1 млн ₽",
              "Ждать до конца 2027 + ремонт (предчистовая)"],
    ),
    dict(
        name="INSIDER", dev="РКС Девелопмент", color=(70, 150, 255),
        tagline="Апартаменты у воды: дом сдан, минимальный бюджет",
        specs=[
            ("Класс", "Бизнес, АПАРТАМЕНТЫ"),
            ("Корпуса", "1 здание, 3–16 эт."),
            ("Лотов", "909 (20–100 м²)"),
            ("Машиномест", "228"),
            ("Коэф. парковки", "0,25"),
            ("Потолки", "2,95 м"),
            ("Отделка", "Чистовая"),
            ("Цена от", "~16–17 млн ₽"),
            ("Срок сдачи", "СДАН, ключи с II кв. 2026"),
        ],
        pros=["Самый низкий вход (~16 млн) и сразу с отделкой",
              "Дом уже построен: без риска, можно заезжать",
              "Первая линия реки, «умный дом», зарядки для электромобилей"],
        cons=["Апартаменты: нет прописки, налог и ЖКУ выше",
              "Паркинг 0,25: одно место на 4 лота",
              "Шум Автозаводской, метро 15+ мин, потолки 2,95"],
    ),
    dict(
        name="SHIFT", dev="ГК «Пионер»", color=(255, 150, 60),
        tagline="Камерный премиум у Нескучного сада, паркинг почти 1:1",
        specs=[
            ("Класс", "Премиум"),
            ("Корпуса", "5 корпусов, до 18 эт."),
            ("Квартир", "561 (45–139 м²)"),
            ("Машиномест", "528 + 19 гостевых"),
            ("Коэф. парковки", "0,94"),
            ("Потолки", "3,2–4,5 м"),
            ("Отделка", "к.1,2,5 без / к.3,4 с"),
            ("Цена от", "~44 млн ₽"),
            ("Срок сдачи", "I кв. 2028"),
        ],
        pros=["Лучший паркинг: 0,94, почти место на квартиру",
              "Камерно: 561 кв., двор без машин, школа и сад",
              "Нескучный сад рядом, потолки до 4,5 м"],
        cons=["Самый дорогой вход: от ~44 млн, нет студий",
              "Плотно: дороги с 2 сторон, рядом ТЭЦ и гаражи",
              "Самый поздний срок (I кв. 2028), метро далеко"],
    ),
    dict(
        name="HIGH LIFE", dev="ГК «Пионер»", color=(60, 200, 130),
        tagline="Башни до 47 этажей у «Павелецкой», часть уже сдана",
        specs=[
            ("Класс", "Премиум"),
            ("Корпуса", "6 башен, 24–47 эт."),
            ("Квартир", "1 528 (24–347 м²)"),
            ("Машиномест", "750"),
            ("Коэф. парковки", "0,49"),
            ("Потолки", "3,0–7,2 м"),
            ("Отделка", "Art / Fusion / White Box"),
            ("Цена от", "~28 млн ₽ (~740 тыс./м²)"),
            ("Срок сдачи", "2025 – IV кв. 2027"),
        ],
        pros=["5–10 мин до «Павелецкой», рядом Садовое",
              "Есть сданные корпуса, отделку выбираете сами",
              "От 24 до 347 м², потолки до 7,2 м, клубный двор"],
        cons=["Железная дорога в ~200 м, от неё шум",
              "Мало зелени, парков рядом нет",
              "Плотно: 1 528 кв., 47 эт., паркинг 0,49"],
    ),
]


def canvas():
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def footer(d, idx, total):
    d.rectangle([0, H - 8, int(W * idx / total), H], fill=(120, 130, 160))
    d.text((W - 60, H - 50), f"{idx}/{total}", font=f(24), fill=MUTED, anchor="rs")


def center(d, y, text, font, fill=TEXT):
    d.text((W // 2, y), text, font=font, fill=fill, anchor="mm")


def slide_title():
    img, d = canvas()
    center(d, 330, "4 ЖК МОСКВЫ", f(110, True))
    center(d, 440, "шпаргалка для покупателя", f(48), MUTED)
    x0 = W // 2 - 4 * 190 + 30
    for i, z in enumerate(ZHK):
        x = x0 + i * 380
        d.rounded_rectangle([x, 560, x + 320, 700], 24, fill=z["color"])
        d.text((x + 160, 630), z["name"], font=f(40, True), fill=BG, anchor="mm")
    center(d, 820, "характеристики · сроки · паркинг · 3 плюса · 3 минуса · тест", f(34), MUTED)
    center(d, 900, "данные открытых источников, сентябрь 2026", f(26), MUTED)
    return img


def slide_anchors():
    img, d = canvas()
    center(d, 110, "ЗАПОМНИ ЗА 10 СЕКУНД", f(64, True))
    for i, z in enumerate(ZHK):
        y = 230 + i * 190
        d.rounded_rectangle([140, y, W - 140, y + 160], 24, fill=CARD)
        d.rounded_rectangle([140, y, 170, y + 160], 12, fill=z["color"])
        d.text((220, y + 55), z["name"], font=f(54, True), fill=z["color"], anchor="lm")
        d.text((220, y + 115), z["dev"], font=f(28), fill=MUTED, anchor="lm")
        d.text((640, y + 80), z["tagline"], font=f(34), fill=TEXT, anchor="lm")
    return img


SHORT = {"Бизнес, АПАРТАМЕНТЫ": "Бизнес, апарт.", "СДАН, ключи с II кв. 2026": "СДАН (ключи 2026)",
         "2 башни, 41–42 эт. + БЦ": "2 башни, 41–42 эт.", "5 корпусов, до 18 эт.": "5 корп., до 18 эт.",
         "6 башен, 24–47 эт.": "6 башен, 24–47 эт.", "~28 млн ₽ (~740 тыс./м²)": "~28 млн ₽"}


def slide_table():
    img, d = canvas()
    center(d, 80, "ГЛАВНЫЕ ЦИФРЫ", f(60, True))
    rows = ["Класс", "Корпуса", "Квартир", "Коэф. парковки", "Потолки", "Цена от", "Срок сдачи"]
    lx, cw, top, rh = 50, 380, 160, 110
    for j, z in enumerate(ZHK):
        x = lx + 300 + j * cw
        d.rounded_rectangle([x + 8, top, x + cw - 8, top + 80], 16, fill=z["color"])
        d.text((x + cw // 2, top + 40), z["name"], font=f(40, True), fill=BG, anchor="mm")
    for i, r in enumerate(rows):
        y = top + 100 + i * rh
        if i % 2 == 0:
            d.rectangle([lx, y, W - lx, y + rh - 8], fill=CARD)
        d.text((lx + 20, y + rh // 2 - 4), r, font=f(32, True), fill=MUTED, anchor="lm")
        for j, z in enumerate(ZHK):
            val = dict(z["specs"])[r] if r in dict(z["specs"]) else dict(z["specs"])["Лотов"]
            val = SHORT.get(val, val)
            x = lx + 300 + j * cw + cw // 2
            font = f(28, True) if r in ("Коэф. парковки", "Срок сдачи") else f(26)
            fill = z["color"] if r in ("Коэф. парковки", "Срок сдачи") else TEXT
            d.text((x, y + rh // 2 - 4), val, font=font, fill=fill, anchor="mm")
    return img


def slide_zhk_intro(z, n):
    img, d = canvas()
    d.rectangle([0, 0, W, H], fill=z["color"])
    d.text((W // 2, 380), f"ЖК {n}/4", font=f(44, True), fill=BG, anchor="mm")
    d.text((W // 2, 510), z["name"], font=f(170, True), fill=BG, anchor="mm")
    d.text((W // 2, 650), z["dev"], font=f(48), fill=BG, anchor="mm")
    d.text((W // 2, 760), z["tagline"], font=f(40, True), fill=BG, anchor="mm")
    return img


def header(d, z, sub):
    d.rectangle([0, 0, W, 130], fill=z["color"])
    d.text((70, 65), z["name"], font=f(64, True), fill=BG, anchor="lm")
    d.text((W - 70, 65), sub, font=f(40, True), fill=BG, anchor="rm")


def slide_specs(z):
    img, d = canvas()
    header(d, z, "ХАРАКТЕРИСТИКИ")
    for i, (k, v) in enumerate(z["specs"]):
        col, row = i % 3, i // 3
        x = 70 + col * 600
        y = 190 + row * 270
        key = k in ("Коэф. парковки", "Срок сдачи")
        d.rounded_rectangle([x, y, x + 560, y + 230], 24, fill=CARD,
                            outline=z["color"] if key else None, width=5)
        d.text((x + 35, y + 55), k.upper(), font=f(28, True), fill=MUTED, anchor="lm")
        size = 50 if len(v) < 16 else 40 if len(v) < 22 else 32
        d.text((x + 35, y + 145), v, font=f(size, True), fill=z["color"] if key else TEXT, anchor="lm")
    return img


def slide_proscons(z):
    img, d = canvas()
    header(d, z, "3 ПЛЮСА · 3 МИНУСА")
    for c, (title, items, color, sign) in enumerate(
            [("ПЛЮСЫ", z["pros"], GOOD, "+"), ("МИНУСЫ", z["cons"], BAD, "–")]):
        x = 70 + c * 900
        d.text((x, 200), title, font=f(52, True), fill=color, anchor="lm")
        for i, t in enumerate(items):
            y = 280 + i * 245
            d.rounded_rectangle([x, y, x + 860, y + 215], 24, fill=CARD)
            d.ellipse([x + 30, y + 67, x + 110, y + 147], fill=color)
            d.text((x + 70, y + 105), sign, font=f(60, True), fill=BG, anchor="mm")
            wrap(d, t, x + 140, y + 107, 690, f(34, True))
    return img


def wrap(d, text, x, cy, maxw, font):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=font) <= maxw:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    lh = font.size + 12
    y0 = cy - (len(lines) - 1) * lh / 2
    for i, ln in enumerate(lines):
        d.text((x, y0 + i * lh), ln, font=font, fill=TEXT, anchor="lm")


def slide_parking():
    img, d = canvas()
    center(d, 90, "КОЭФФИЦИЕНТ МАШИНОМЕСТ", f(60, True))
    center(d, 160, "машиноместа ÷ квартиры   (1,0 = место на каждую квартиру)", f(30), MUTED)
    data = [("SHIFT", 0.94, "528 / 561"), ("АУРА", 0.62, "566 / 916"),
            ("HIGH LIFE", 0.49, "750 / 1 528"), ("INSIDER", 0.25, "228 / 909")]
    colors = {z["name"]: z["color"] for z in ZHK}
    x0, maxw = 420, 1250
    d.line([x0 + maxw, 230, x0 + maxw, 960], fill=MUTED, width=2)
    d.text((x0 + maxw, 990), "1,0", font=f(28), fill=MUTED, anchor="mm")
    for i, (n, v, raw) in enumerate(data):
        y = 250 + i * 180
        d.text((x0 - 40, y + 65), n, font=f(46, True), fill=colors[n], anchor="rm")
        d.rounded_rectangle([x0, y, x0 + int(maxw * v), y + 130], 18, fill=colors[n])
        d.text((x0 + int(maxw * v) - 30, y + 65), f"{v:.2f}".replace(".", ","),
               font=f(56, True), fill=BG, anchor="rm")
        d.text((x0 + int(maxw * v) + 25, y + 65), raw, font=f(30), fill=MUTED, anchor="lm")
    return img


def slide_timeline():
    img, d = canvas()
    center(d, 90, "СРОКИ СДАЧИ", f(64, True))
    years = [2025, 2026, 2027, 2028]
    x0, x1, ty = 200, 1720, 870
    span = x1 - x0

    def xq(year, q):
        return x0 + span * ((year - 2025) * 4 + (q - 1)) / 16

    d.line([x0, ty, x1, ty], fill=MUTED, width=4)
    for yr in years:
        x = xq(yr, 1)
        d.line([x, ty - 15, x, ty + 15], fill=MUTED, width=4)
        d.text((x, ty + 50), str(yr), font=f(36, True), fill=MUTED, anchor="mm")
    now = xq(2026, 3) + span / 16 * 0.9
    d.line([now, 190, now, ty], fill=(255, 255, 255), width=2)
    d.text((now, 180), "сейчас", font=f(26), fill=TEXT, anchor="mb")
    c = {z["name"]: z["color"] for z in ZHK}
    items = [
        ("INSIDER", xq(2025, 2), xq(2026, 2), "ввод II кв. 2025 → ключи II кв. 2026: СДАН"),
        ("HIGH LIFE", xq(2025, 1), xq(2027, 4), "очереди: 2025 → IV кв. 2027"),
        ("АУРА", xq(2027, 4), None, "IV кв. 2027"),
        ("SHIFT", xq(2028, 1), None, "I кв. 2028: самый поздний"),
    ]
    for i, (n, a, b, label) in enumerate(items):
        y = 250 + i * 145
        if b:
            d.rounded_rectangle([a, y, b, y + 70], 35, fill=c[n])
        else:
            d.ellipse([a - 35, y, a + 35, y + 70], fill=c[n])
        d.text((a - 50 if b is None else a, y - 12), n, font=f(34, True), fill=c[n],
               anchor="rb" if b is None else "lb")
        lx = (b or a) + 50
        if lx > 1500:
            d.text((a - 50, y + 50), label, font=f(28), fill=TEXT, anchor="rm")
        else:
            d.text((lx, y + 35), label, font=f(28), fill=TEXT, anchor="lm")
    return img


def slide_who():
    img, d = canvas()
    center(d, 100, "КОМУ ЧТО ПОДХОДИТ", f(64, True))
    rows = [("Метро под домом", "АУРА"),
            ("Мин. бюджет, заехать сразу, под аренду", "INSIDER"),
            ("Машина и семья с детьми", "SHIFT"),
            ("Центр, статус, готовый корпус", "HIGH LIFE")]
    c = {z["name"]: z["color"] for z in ZHK}
    for i, (need, n) in enumerate(rows):
        y = 220 + i * 195
        d.rounded_rectangle([140, y, W - 140, y + 165], 24, fill=CARD)
        d.text((200, y + 82), need, font=f(44), fill=TEXT, anchor="lm")
        d.rounded_rectangle([W - 620, y + 30, W - 190, y + 135], 20, fill=c[n])
        d.text((W - 405, y + 82), n, font=f(48, True), fill=BG, anchor="mm")
    return img


QUIZ = [
    ("Где самый высокий коэффициент машиномест?", "SHIFT: 0,94", 2),
    ("Какой ЖК продаёт апартаменты, а не квартиры?", "INSIDER", 1),
    ("Срок сдачи АУРЫ?", "IV квартал 2027", 0),
    ("Какой ЖК у «Павелецкой»?", "HIGH LIFE", 3),
    ("Главный минус HIGH LIFE?", "Ж/д пути в ~200 м (шум)", 3),
    ("Самый поздний срок сдачи?", "SHIFT: I кв. 2028", 2),
    ("Коэффициент машиномест INSIDER?", "0,25", 1),
    ("Какой ЖК в 300 м от метро «Тульская»?", "АУРА", 0),
]


def slide_quiz(i, q, ans, zi, show):
    img, d = canvas()
    center(d, 140, f"ТЕСТ  {i}/{len(QUIZ)}", f(44, True), MUTED)
    center(d, 420, q, f(64, True))
    if show:
        col = ZHK[zi]["color"]
        tw = d.textlength(ans, font=f(80, True)) + 120
        d.rounded_rectangle([W / 2 - tw / 2, 580, W / 2 + tw / 2, 760], 30, fill=col)
        center(d, 670, ans, f(80, True), BG)
    else:
        center(d, 670, "подумай...", f(56), MUTED)
    return img


def slide_end():
    img, d = canvas()
    center(d, 420, "Готово!", f(110, True))
    center(d, 560, "Пересмотри тест, пока не ответишь на все 8 вопросов", f(44), MUTED)
    center(d, 640, "Цены и сроки перед сделкой сверяй с застройщиком", f(34), MUTED)
    return img


def build():
    slides = [(slide_title(), 5), (slide_anchors(), 10), (slide_table(), 16)]
    for n, z in enumerate(ZHK, 1):
        slides += [(slide_zhk_intro(z, n), 3), (slide_specs(z), 12), (slide_proscons(z), 14)]
    slides += [(slide_parking(), 9), (slide_timeline(), 10), (slide_who(), 8)]
    for i, (q, a, zi) in enumerate(QUIZ, 1):
        slides += [(slide_quiz(i, q, a, zi, False), 4), (slide_quiz(i, q, a, zi, True), 3)]
    slides.append((slide_end(), 4))

    total = len(slides)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as tmp:
        clips = []
        for i, (img, dur) in enumerate(slides, 1):
            footer(ImageDraw.Draw(img), i, total)
            png = os.path.join(tmp, f"s{i:03}.png")
            mp4 = os.path.join(tmp, f"s{i:03}.mp4")
            img.save(png)
            fade = 0.35
            vf = f"fade=t=in:st=0:d={fade},fade=t=out:st={dur - fade}:d={fade},format=yuv420p"
            subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-loop", "1", "-i", png,
                            "-t", str(dur), "-r", str(FPS), "-vf", vf,
                            "-c:v", "libx264", "-preset", "medium", "-crf", "20", mp4], check=True)
            clips.append(mp4)
        lst = os.path.join(tmp, "list.txt")
        with open(lst, "w") as fh:
            fh.writelines(f"file '{c}'\n" for c in clips)
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", lst, "-c", "copy", "-movflags", "+faststart", OUT], check=True)
    print(f"{OUT}: {total} слайдов, {sum(d for _, d in slides)} сек")


if __name__ == "__main__":
    build()
