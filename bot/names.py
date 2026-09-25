"""Поиск ЖК по названию: «хай лайф» → HIGH LIFE, «джойс» → Джойс."""
import re
from difflib import SequenceMatcher

_CYR2LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

# Как английские слова из названий ЖК обычно пишут по-русски
_EN2RU = {
    "high": "хай", "life": "лайф", "tower": "тауэр", "towers": "тауэрс", "park": "парк",
    "city": "сити", "house": "хаус", "river": "ривер", "level": "левел", "one": "уан",
    "sky": "скай", "garden": "гарден", "gardens": "гарденс", "residence": "резиденс",
    "residences": "резиденсез", "club": "клаб", "loft": "лофт", "west": "вест", "east": "ист",
    "side": "сайд", "up": "ап", "upside": "апсайд", "town": "таун", "hill": "хилл",
    "hills": "хиллс", "time": "тайм", "joy": "джой", "dream": "дрим", "grand": "гранд",
    "forest": "форест", "lake": "лейк", "light": "лайт", "point": "поинт", "plaza": "плаза",
    "square": "сквер", "home": "хоум", "sun": "сан", "green": "грин", "star": "стар",
    "mind": "майнд", "feel": "фил", "heart": "харт", "art": "арт", "space": "спейс",
    "lux": "люкс", "prime": "прайм", "premium": "премиум", "collection": "коллекшн",
    "district": "дистрикт", "design": "дизайн", "russian": "рашн", "the": "зе", "of": "оф",
    "by": "бай", "first": "ферст", "big": "биг", "new": "нью", "bay": "бэй", "view": "вью",
    "top": "топ", "cloud": "клауд", "family": "фэмили", "smart": "смарт", "next": "некст",
    "story": "стори", "place": "плейс", "avenue": "авеню", "soul": "соул", "wave": "вейв",
    "match": "матч", "island": "айленд", "port": "порт", "river-park": "ривер парк",
}


def _lat(s: str) -> str:
    s = "".join(_CYR2LAT.get(ch, ch) for ch in s.lower())
    return re.sub(r"[^a-z0-9]", "", s)


def _en2ru(s: str) -> str:
    return " ".join(_EN2RU.get(w, w) for w in re.findall(r"[a-zа-яё0-9]+", s.lower()))


def _forms(name: str, guid: str = "") -> set[str]:
    forms = {_lat(name), _lat(_en2ru(name))}
    if guid:
        forms.add(_lat(re.sub(r"[-_]msk$", "", guid)))
    return {f for f in forms if f}


def score(query: str, name: str, guid: str = "") -> float:
    best = 0.0
    for q in _forms(query):
        for f in _forms(name, guid):
            r = SequenceMatcher(None, q, f).ratio()
            if len(q) >= 4 and (q == f[: len(q)] or f == q[: len(f)]):
                r = max(r, 0.9)
            best = max(best, r)
    return best


def find_blocks(query: str, blocks: list[dict], limit: int = 3) -> list[tuple[float, dict]]:
    """Блоки (dict с name/guid), отсортированные по похожести на запрос."""
    ranked = sorted(((score(query, b.get("name", ""), b.get("guid", "")), b) for b in blocks),
                    key=lambda x: -x[0])
    return ranked[:limit]
