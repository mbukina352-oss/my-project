"""Видео-шпаргалка с голосом рассказчика и субтитрами.

Использует слайды из make_video.py, озвучку делает офлайн через RHVoice.
Зависимости: apt-get install rhvoice rhvoice-russian; pip install pillow imageio-ffmpeg
Запуск:      python3 zhk-summary/make_narrated_video.py
"""
import os
import subprocess
import tempfile
import wave

import imageio_ffmpeg
from PIL import Image, ImageDraw

import make_video as mv

VOICE = os.environ.get("VOICE", "aleksandr-hq")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ZHK_summary_voice.mp4")
PAUSE = 0.35
THINK = 3.0
TEMPO = 1.15  # чуть быстрее стандартного темпа RHVoice


INTRO = [
    "Привет! Сейчас за несколько минут разберём четыре новостройки Москвы.",
    "Аура на Тульской, Инсайдер, и два проекта группы Пионер: Шифт и Хай Лайф.",
    "По каждому: главные характеристики, сроки сдачи, парковка, три плюса и три минуса. А в конце короткий тест.",
]
ANCHORS = [
    "Сначала запомним якоря, чтобы не путать проекты.",
    "Аура, фиолетовая: небоскрёбы в трёхстах метрах от метро Тульская.",
    "Инсайдер, синий: апартаменты у реки, дом уже сдан, и это самый дешёвый вход.",
    "Шифт, оранжевый: камерный премиум у Нескучного сада, почти по машиноместу на квартиру.",
    "Хай Лайф, зелёный: башни до сорока семи этажей у метро Павелецкая.",
]
TABLE = [
    "Вот главные цифры рядом.",
    "Три проекта из четырёх относятся к премиум-классу. Только Инсайдер бизнес-класса, и это апартаменты.",
    "Самые высокие потолки в Хай Лайфе: до семи метров двадцати в двухсветных лотах.",
    "По срокам: Инсайдер уже сдан, Хай Лайф сдаётся очередями до конца двадцать седьмого года, "
    "Аура в четвёртом квартале двадцать седьмого, а Шифт самый поздний, в первом квартале двадцать восьмого.",
]
ZHK_TEXT = [
    dict(
        intro=["Начнём с Ауры от компании Мангазея."],
        specs=[
            "Это две башни в сорок один и сорок два этажа плюс собственный бизнес-центр.",
            "Около девятисот шестнадцати квартир, площадью от двадцати восьми до ста сорока шести квадратных метров.",
            "Машиномест пятьсот шестьдесят шесть, значит коэффициент ноль шестьдесят две сотых.",
            "Потолки от трёх двадцати до трёх с половиной метров, отделка предчистовая.",
            "Вход примерно от двадцати миллионов рублей. Сдача в четвёртом квартале две тысячи двадцать седьмого года.",
        ],
        pc=[
            "Плюсы. Первый: метро Тульская в трёхстах метрах, и рядом МЦК.",
            "Второй: быстрый выезд на машине, три минуты до третьего кольца и восемь до Садового.",
            "Третий: высота и виды, потолки до трёх с половиной метров, а в бизнес-центре фитнес с бассейном.",
            "Теперь минусы. Шум и пыль от Тульской эстакады и магистралей.",
            "Дорогой квадратный метр: на верхних этажах доходит почти до миллиона рублей.",
            "И ждать до конца двадцать седьмого года, а потом ещё делать ремонт.",
        ],
    ),
    dict(
        intro=["Второй проект: Инсайдер от РКС Девелопмент."],
        specs=[
            "Одно здание переменной этажности, от трёх до шестнадцати этажей, прямо на берегу Москвы-реки.",
            "Девятьсот девять лотов от двадцати до ста квадратных метров, в основном студии и однушки.",
            "Важно: это апартаменты, а не квартиры.",
            "Паркинг всего на двести двадцать восемь мест, коэффициент ноль двадцать пять сотых.",
            "Потолки два девяносто пять, отделка чистовая, а вход от шестнадцати миллионов.",
            "Дом введён во втором квартале двадцать пятого года, ключи выдают с лета двадцать шестого.",
        ],
        pc=[
            "Плюсы. Самый доступный бюджет из четырёх, и сразу с отделкой.",
            "Дом уже построен: никакого риска недостроя, можно заезжать или сдавать в аренду.",
            "Первая линия реки, умный дом и зарядки для электромобилей в паркинге.",
            "Минусы. Статус апартаментов: нет постоянной прописки, налог и коммуналка выше.",
            "Парковки мало: одно место на четыре лота.",
            "И шумная Автозаводская улица рядом, а до метро больше пятнадцати минут пешком.",
        ],
    ),
    dict(
        intro=["Третий проект: Шифт от группы Пионер."],
        specs=[
            "Пять корпусов до восемнадцати этажей на улице Орджоникидзе, рядом с Нескучным садом.",
            "Пятьсот шестьдесят одна квартира, от сорока пяти до ста тридцати девяти метров. Студий нет.",
            "Паркинг на пятьсот двадцать восемь мест, коэффициент ноль девяносто четыре. Это лучший результат из четырёх.",
            "Потолки от трёх двадцати до четырёх с половиной метров.",
            "Вход около сорока четырёх миллионов. Сдача в первом квартале две тысячи двадцать восьмого года.",
        ],
        pc=[
            "Плюсы. Почти по машиноместу на каждую квартиру.",
            "Камерность: немного квартир, двор без машин, своя частная школа и детский сад.",
            "Нескучный сад в шаговой доступности и высокие потолки.",
            "Минусы. Самый дорогой вход из четырёх проектов.",
            "Плотная застройка: дороги с двух сторон, рядом ТЭЦ и гаражи.",
            "И самый поздний срок, а метро не в шаговой доступности.",
        ],
    ),
    dict(
        intro=["И четвёртый: Хай Лайф, тоже от Пионера."],
        specs=[
            "Шесть башен от двадцати четырёх до сорока семи этажей у метро Павелецкая.",
            "Тысяча пятьсот двадцать восемь квартир, от двадцати четырёх до трёхсот сорока семи метров.",
            "Семьсот пятьдесят машиномест, коэффициент ноль сорок девять сотых.",
            "Потолки от трёх метров, а в двухсветных лотах до семи двадцати.",
            "Отделку выбираете сами: дизайнерская Арт или Фьюжн, либо вайт бокс.",
            "Вход от двадцати восьми миллионов. Корпуса сдаются очередями: первые в двадцать пятом году, последние к концу двадцать седьмого.",
        ],
        pc=[
            "Плюсы. Пять или десять минут пешком до Павелецкой, рядом Садовое кольцо и набережная.",
            "Можно купить в уже сданном корпусе и увидеть готовый результат.",
            "Огромный выбор площадей и закрытый клубный двор.",
            "Минусы. Железная дорога примерно в двухстах метрах, от неё шум.",
            "Мало зелени: парков рядом нет.",
            "И высокая плотность: полторы тысячи квартир, а коэффициент парковки ноль сорок девять.",
        ],
    ),
]
PARKING = [
    "Теперь сравним парковку. Коэффициент: это машиноместа, делённые на количество квартир.",
    "Лидер Шифт, ноль девяносто четыре. Дальше Аура, ноль шестьдесят две, и Хай Лайф, ноль сорок девять.",
    "Замыкает Инсайдер: всего ноль двадцать пять, одно место на четыре лота.",
]
TIMELINE = [
    "Сроки сдачи на одной шкале.",
    "Инсайдер уже готов. Хай Лайф сдаётся очередями до конца двадцать седьмого года.",
    "Аура в четвёртом квартале двадцать седьмого. Шифт самый поздний, в начале двадцать восьмого.",
]
WHO = [
    "Итак, кому что подходит.",
    "Нужно метро под домом: Аура.",
    "Минимальный бюджет, заехать сразу или сдавать в аренду: Инсайдер.",
    "Есть машина и дети: Шифт.",
    "Центр, статус и готовый корпус: Хай Лайф.",
]
QUIZ = [
    ("Вопрос первый. Где самый высокий коэффициент машиномест?", "Правильно, в Шифте: ноль девяносто четыре."),
    ("Вопрос второй. Какой проект продаёт апартаменты, а не квартиры?", "Инсайдер."),
    ("Вопрос третий. Когда сдаётся Аура?", "В четвёртом квартале двадцать седьмого года."),
    ("Вопрос четвёртый. Какой комплекс рядом с метро Павелецкая?", "Хай Лайф."),
    ("Вопрос пятый. Главный минус Хай Лайфа?", "Железная дорога примерно в двухстах метрах."),
    ("Вопрос шестой. У кого самый поздний срок сдачи?", "У Шифта: первый квартал двадцать восьмого года."),
    ("Вопрос седьмой. Какой коэффициент машиномест у Инсайдера?", "Ноль двадцать пять."),
    ("Вопрос восьмой. Какой комплекс в трёхстах метрах от метро Тульская?", "Аура."),
]
QUIZ_INTRO = "А теперь проверим себя. Я задаю вопрос, вы отвечаете вслух, пока идёт пауза."
END = [
    "Вот и всё! Пересматривайте тест, пока не ответите на все вопросы без ошибок.",
    "И перед сделкой обязательно сверьте цены и сроки с застройщиком. Удачи!",
]


def plan():
    """Список (слайд, [реплики]); реплика None означает паузу «подумайте»."""
    items = [(mv.slide_title(), INTRO), (mv.slide_anchors(), ANCHORS), (mv.slide_table(), TABLE)]
    for n, (z, t) in enumerate(zip(mv.ZHK, ZHK_TEXT), 1):
        items += [(mv.slide_zhk_intro(z, n), t["intro"]),
                  (mv.slide_specs(z), t["specs"]),
                  (mv.slide_proscons(z), t["pc"])]
    items += [(mv.slide_parking(), PARKING), (mv.slide_timeline(), TIMELINE), (mv.slide_who(), WHO)]
    for i, ((q, a), (_, show, zi)) in enumerate(zip(QUIZ, mv.QUIZ), 1):
        lines = ([QUIZ_INTRO] if i == 1 else []) + [q, None]
        items += [(mv.slide_quiz(i, mv.QUIZ[i - 1][0], show, zi, False), lines),
                  (mv.slide_quiz(i, mv.QUIZ[i - 1][0], show, zi, True), [a])]
    items.append((mv.slide_end(), END))
    return items


# ---------- ведущий ----------

SPRITE_W, SPRITE_H = 560, 1080
SPRITE_X = mv.W - SPRITE_W + 20
SKIN = (240, 200, 170)
SKIN_D = (205, 155, 125)
HAIR = (62, 42, 32)
SUIT = (38, 52, 92)
SUIT_D = (28, 38, 70)
TIE = (150, 110, 255)
K = 2  # рисуем в 2x и уменьшаем для сглаживания


def presenter(mouth, blink, point, look):
    img = Image.new("RGBA", (SPRITE_W * K, SPRITE_H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def P(*pts):
        return [v * K for v in pts]

    def Q(*pts):
        return [(v + 55 if i % 2 else v) * K for i, v in enumerate(pts)]

    cx = 330
    # рука, указывающая на слайд (рисуется за корпусом)
    if point:
        d.line(P(cx - 150, 760, cx - 250, 690, 70, 560), fill=SUIT, width=72 * K, joint="curve")
        d.ellipse(P(cx - 186, 724, cx - 114, 796), fill=SUIT)
        d.ellipse(P(70 - 36, 560 - 36, 70 + 36, 560 + 36), fill=SUIT)
        d.line(P(58, 545, 30, 520), fill=(245, 245, 250), width=26 * K)
        d.ellipse(P(0, 478, 56, 530), fill=SKIN)
        d.rounded_rectangle(P(-40, 488, 20, 504), 8 * K, fill=SKIN)
    # корпус
    d.ellipse(P(cx - 210, 660, cx + 210, 900), fill=SUIT)
    d.rectangle(P(cx - 210, 780, cx + 210, SPRITE_H), fill=SUIT)
    d.polygon(P(cx - 55, 690, cx + 55, 690, cx, 830), fill=(245, 245, 250))
    d.polygon(P(cx - 11, 708, cx + 11, 708, cx + 18, 800, cx, 835, cx - 18, 800), fill=TIE)
    d.polygon(P(cx - 60, 688, cx, 835, cx - 90, 760), fill=SUIT_D)
    d.polygon(P(cx + 60, 688, cx, 835, cx + 90, 760), fill=SUIT_D)
    # шея
    d.rectangle(P(cx - 36, 610, cx + 36, 700), fill=SKIN)
    d.ellipse(P(cx - 36, 660, cx + 36, 712), fill=SKIN_D)
    # голова
    d.ellipse(Q(cx - 118, 283, cx + 118, 455), fill=HAIR)
    d.ellipse(Q(cx - 127, 420, cx - 97, 482), fill=SKIN)
    d.ellipse(Q(cx + 97, 420, cx + 127, 482), fill=SKIN)
    d.ellipse(Q(cx - 105, 330, cx + 105, 592), fill=SKIN)
    d.pieslice(Q(cx - 112, 290, cx + 112, 440), 185, 355, fill=HAIR)
    d.polygon(Q(cx - 100, 370, cx - 30, 330, cx + 60, 352, cx + 104, 395, cx + 108, 340, cx - 108, 345), fill=HAIR)
    # брови
    by = -5 if mouth >= 3 else 0
    d.line(Q(cx - 68, 410 + by, cx - 28, 403 + by), fill=HAIR, width=8 * K)
    d.line(Q(cx + 28, 403 + by, cx + 68, 410 + by), fill=HAIR, width=8 * K)
    # глаза
    for ex in (cx - 48, cx + 48):
        if blink:
            d.line(Q(ex - 19, 440, ex + 19, 440), fill=(60, 40, 40), width=5 * K)
        else:
            d.ellipse(Q(ex - 20, 426, ex + 20, 454), fill=(255, 255, 255))
            px = ex + look
            d.ellipse(Q(px - 10, 430, px + 10, 450), fill=(70, 50, 40))
            d.ellipse(Q(px - 5, 435, px + 5, 445), fill=(15, 15, 20))
            d.ellipse(Q(px - 5, 432, px - 1, 436), fill=(255, 255, 255))
    # нос и румянец
    d.line(Q(cx + 2, 452, cx - 8, 496, cx + 8, 500), fill=SKIN_D, width=5 * K, joint="curve")
    d.ellipse(Q(cx - 88, 485, cx - 52, 510), fill=(245, 180, 160))
    d.ellipse(Q(cx + 52, 485, cx + 88, 510), fill=(245, 180, 160))
    # рот
    my = 540
    if mouth == 0:
        d.arc(Q(cx - 26, my - 20, cx + 26, my + 6), 20, 160, fill=(150, 60, 60), width=6 * K)
    else:
        w, h = 22 + 2 * mouth, 4 + 6 * mouth
        d.ellipse(Q(cx - w, my - h, cx + w, my + h), fill=(95, 30, 40))
        if mouth >= 2:
            d.chord(Q(cx - w + 4, my - h + 1, cx + w - 4, my - h + 14), 0, 180, fill=(255, 255, 255))
            d.ellipse(Q(cx - w / 2, my + h - 12, cx + w / 2, my + h - 1), fill=(220, 110, 120))
    return img.resize((SPRITE_W, SPRITE_H), Image.LANCZOS)


_cache = {}


def sprite(*state):
    if state not in _cache:
        _cache[state] = presenter(*state)
    return _cache[state]


# ---------- кадр ----------

SLIDE_W, SLIDE_H = 1400, 788
SX, SY = 30, 30
SUB_Y = 848


def compose(slide, text):
    img = Image.new("RGB", (mv.W, mv.H), mv.BG)
    d = ImageDraw.Draw(img)
    # «студия» за ведущим
    glow = Image.new("RGB", (mv.W, mv.H), mv.BG)
    gd = ImageDraw.Draw(glow)
    for i in range(24):
        c = tuple(int(a + (b - a) * i / 23) for a, b in zip((44, 38, 80), mv.BG))
        r = 460 - i * 12
        gd.ellipse([1690 - r, 500 - r, 1690 + r, 500 + r], fill=c)
    img.paste(glow.crop((SX + SLIDE_W + 20, 0, mv.W, mv.H)), (SX + SLIDE_W + 20, 0))
    img.paste(slide.resize((SLIDE_W, SLIDE_H), Image.LANCZOS), (SX, SY))
    d.rounded_rectangle([SX, SUB_Y, SX + SLIDE_W, mv.H - 30], 22, fill=mv.CARD)
    font = mv.f(34, True)
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=font) <= SLIDE_W - 80:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    lh = 46
    cy = (SUB_Y + mv.H - 30) / 2
    y0 = cy - (len(lines) - 1) * lh / 2
    for i, ln in enumerate(lines):
        d.text((SX + 40, y0 + i * lh), ln, font=font, fill=mv.TEXT, anchor="lm")
    return img


def nameplate(img):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([1480, 960, 1890, 1040], 18, fill=TIE)
    d.text((1685, 1000), "Гид по новостройкам", font=mv.f(28, True), fill=mv.BG, anchor="mm")


# ---------- сборка ----------

def build():
    import array
    import math
    import random

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    fps, sr = 25, 24000
    items = plan()
    total = len(items)
    phrases, pcm = [], array.array("h")
    with tempfile.TemporaryDirectory() as tmp:
        for si, (slide, lines) in enumerate(items, 1):
            mv.footer(ImageDraw.Draw(slide), si, total)
            for li, line in enumerate(lines):
                raw, out = os.path.join(tmp, "raw.wav"), os.path.join(tmp, "out.wav")
                if line is None:
                    n = int(THINK * fps)
                    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                                    f"anullsrc=r={sr}:cl=mono", "-t", str(n / fps),
                                    "-c:a", "pcm_s16le", out], check=True)
                    text = "…подумайте…"
                else:
                    subprocess.run(["RHVoice-test", "-p", VOICE, "-o", raw],
                                   input=line.encode(), check=True, capture_output=True)
                    with wave.open(raw) as w:
                        dur = w.getnframes() / w.getframerate() / TEMPO + PAUSE
                    n = round(dur * fps)
                    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", raw, "-af",
                                    f"atempo={TEMPO},apad,atrim=0:{n / fps:.4f}", "-ar", str(sr),
                                    "-ac", "1", "-c:a", "pcm_s16le", out], check=True)
                    text = line
                with wave.open(out) as w:
                    chunk = array.array("h", w.readframes(w.getnframes()))
                need = n * sr // fps
                chunk = chunk[:need] + array.array("h", [0] * max(0, need - len(chunk)))
                pcm.extend(chunk)
                base = compose(slide, text)
                nameplate(base)
                phrases.append((base, n, li == 0))
            print(f"озвучка: слайд {si}/{total}", flush=True)

        audio = os.path.join(tmp, "voice.wav")
        with wave.open(audio, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(pcm.tobytes())

        spf = sr // fps
        nframes = len(pcm) // spf
        rms = []
        for i in range(nframes):
            seg = pcm[i * spf:(i + 1) * spf]
            rms.append(math.sqrt(sum(v * v for v in seg[::4]) / (len(seg) / 4)))
        peak = sorted(rms)[int(len(rms) * 0.97)] or 1

        enc = subprocess.Popen(
            [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{mv.W}x{mv.H}", "-r", str(fps), "-i", "-", "-i", audio,
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", OUT],
            stdin=subprocess.PIPE)
        rnd = random.Random(7)
        next_blink, g, mouth = rnd.randint(40, 110), 0, 0
        for base, n, first in phrases:
            for k in range(n):
                lvl = min(4, int(rms[g] / peak * 5)) if rms[g] > peak * 0.08 else 0
                mouth = lvl if lvl >= mouth else max(lvl, mouth - 1)
                blink = next_blink <= g < next_blink + 3
                if g >= next_blink + 3:
                    next_blink = g + rnd.randint(60, 130)
                point = first and k < 32
                look = -7 if point or (g // 90) % 4 == 3 else 0
                frame = base.copy()
                dy = round(4 * math.sin(2 * math.pi * g / (fps * 2.4)))
                sp = sprite(mouth, blink, point, look)
                frame.paste(sp, (SPRITE_X, dy), sp)
                nameplate(frame)
                enc.stdin.write(frame.tobytes())
                g += 1
            if g % (fps * 30) < n:
                print(f"видео: {g / fps / 60:.1f} мин", flush=True)
        enc.stdin.close()
        enc.wait()
    print(f"{OUT}: {g / fps / 60:.1f} мин")


if __name__ == "__main__":
    build()
