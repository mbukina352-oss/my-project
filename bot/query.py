"""Разбор запроса вида «Джойс 35млн 60м2»."""
import re
from dataclasses import dataclass

_NUM = r"(\d+(?:[.,]\d+)?)"

_AREA_RE = re.compile(_NUM + r"\s*(?:м2|м²|м\.?\s*кв\.?|кв\.?\s*м\.?|квм|кв\b|m2|метр\w*)", re.I)
_PRICE_RE = re.compile(_NUM + r"\s*(?:млн\.?|mln|кк|м)(?![а-яa-z²2])", re.I)
_PRICE_RUB_RE = re.compile(r"\b(\d[\d\s]{5,}\d)\s*(?:руб\.?|р\.?|₽)?", re.I)
_ROOMS_RE = re.compile(r"\b(\d)\s*-?\s*(?:к|комн\w*|ккв|кк\b)(?![а-я])", re.I)
_STUDIO_RE = re.compile(r"\bстуди\w*\b", re.I)


_FILLER_RE = re.compile(
    r"(?<![а-яё])(жк|пришли\w*|скинь\w*|покажи\w*|найди\w*|нужн\w*|планировк\w*|квартир\w*|"
    r"пожалуйста|плиз|в|до|за|около|примерно|пдф|pdf)(?![а-яё])",
    re.I,
)


@dataclass
class Query:
    complex_name: str
    price: int | None = None  # рубли
    area: float | None = None  # м²
    rooms: int | None = None  # 0 = студия

    def describe(self) -> str:
        parts = [f"ЖК «{self.complex_name}»" if self.complex_name else "любой ЖК"]
        if self.rooms is not None:
            parts.append("студия" if self.rooms == 0 else f"{self.rooms}-комн.")
        if self.area:
            parts.append(f"~{self.area:g} м²")
        if self.price:
            parts.append(f"до ~{self.price / 1_000_000:g} млн ₽")
        return ", ".join(parts)


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def parse_query(text: str) -> Query:
    rest = " " + text.strip() + " "

    area = None
    if m := _AREA_RE.search(rest):
        area = _num(m.group(1))
        rest = rest[: m.start()] + " " + rest[m.end():]

    rooms = None
    if m := _STUDIO_RE.search(rest):
        rooms = 0
        rest = rest[: m.start()] + " " + rest[m.end():]
    elif m := _ROOMS_RE.search(rest):
        rooms = int(m.group(1))
        rest = rest[: m.start()] + " " + rest[m.end():]

    price = None
    if m := _PRICE_RE.search(rest):
        price = int(_num(m.group(1)) * 1_000_000)
        rest = rest[: m.start()] + " " + rest[m.end():]
    elif m := _PRICE_RUB_RE.search(rest):
        value = int(re.sub(r"\s", "", m.group(1)))
        if value >= 1_000_000:
            price = value
            rest = rest[: m.start()] + " " + rest[m.end():]

    name = _FILLER_RE.sub(" ", rest)
    name = re.sub(r"[«»\"',;]+", " ", name)
    name = " ".join(name.split())
    return Query(complex_name=name, price=price, area=area, rooms=rooms)
